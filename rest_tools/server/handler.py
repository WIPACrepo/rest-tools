import logging
import json
import time
from functools import wraps, update_wrapper, partialmethod, partial
from collections import defaultdict
from typing import Any

import tornado.web
import tornado.gen
import tornado.httpclient
from tornado.platform.asyncio import to_asyncio_future

from rest_tools.client import json_decode  # type: ignore
from .auth import Auth, OpenIDAuth
from .stats import RouteStats
import rest_tools

logger = logging.getLogger('rest')

def RestHandlerSetup(config={}):
    """
    Default RestHandler setup. Returns the default arguments
    for passing to the route setup.

    Args:
        config (dict): config dict

    Returns:
        dict: handler config
    """
    debug = True if 'debug' in config and config['debug'] else False
    auth = None
    auth_url = ''
    module_auth_key = ''
    if 'auth' in config:
        if 'secret' in config['auth']:
            kwargs = {
                'secret': config['auth']['secret']
            }
            if 'issuer' in config['auth']:
                kwargs['issuer'] = config['auth']['issuer']
            if 'algorithm' in config['auth']:
                kwargs['algorithm'] = config['auth']['algorithm']
            if 'expiration' in config['auth']:
                kwargs['expiration'] = config['auth']['expiration']
            if 'expiration_temp' in config['auth']:
                kwargs['expiration_temp'] = config['auth']['expiration_temp']
            auth = Auth(**kwargs)
        elif 'openid_url' in config['auth']:
            auth = OpenIDAuth(config['auth']['openid_url'])
            if auth.token_url:
                auth_url = auth.token_url
        if 'url' in config['auth']:
            auth_url = config['auth']['url']
    if 'rest_api' in config and 'auth_key' in config['rest_api']:
        module_auth_key = config['rest_api']['auth_key']

    if 'route_stats' in config:
        route_stats = defaultdict(partial(RouteStats, **config['route_stats']))
    else:
        route_stats = defaultdict(RouteStats)

    return {
        'debug': debug,
        'auth': auth,
        'auth_url': auth_url,
        'module_auth_key': module_auth_key,
        'server_header': config.get('server_header', 'REST'),
        'route_stats': route_stats
    }

class RestHandler(tornado.web.RequestHandler):
    """Default REST handler"""
    def __init__(self, *args, **kwargs):
        self.server_header = ''
        try:
            super(RestHandler, self).__init__(*args, **kwargs)
        except Exception:
            logging.error('error', exc_info=True)

    def initialize(self, debug=False, auth=None, auth_url=None, module_auth_key='', server_header='', route_stats=None, **kwargs):
        super(RestHandler, self).initialize(**kwargs)
        self.debug = debug
        self.auth = auth
        self.auth_url = auth_url
        self.auth_data = {}
        self.auth_key = None
        self.module_auth_key = module_auth_key
        self.server_header = server_header
        self.route_stats = route_stats

    def set_default_headers(self):
        self._headers['Server'] = self.server_header

    def get_template_namespace(self):
        namespace = super(RESTHandler,self).get_template_namespace()
        namespace['version'] = rest_tools.__version__
        return namespace

    def get_current_user(self):
        try:
            type,token = self.request.headers['Authorization'].split(' ', 1)
            if type.lower() != 'bearer':
                raise Exception('bad header type')
            logger.debug('token: %r', token)
            data = self.auth.validate(token)
            self.auth_data = data
            self.auth_key = token
            return data['sub']
        except Exception:
            if self.debug and 'Authorization' in self.request.headers:
                logger.info('Authorization: %r', self.request.headers['Authorization'])
            logger.info('failed auth', exc_info=True)
        return None

    def prepare(self):
        stat = self.route_stats[self.request.path]
        if stat.is_overloaded():
            backoff = stat.get_backoff_time()
            logger.warn('Server is overloaded, backoff %r', backoff)
            self.set_header('Retry-After', backoff)
            raise tornado.web.HTTPError(503, reason="server overloaded")
        self.start_time = time.time()

    def on_finish(self):
        if self.get_status() < 500:
            stat = self.route_stats[self.request.path]
            stat.append(time.time()-self.start_time)

    def write_error(self, status_code=500, **kwargs):
        """Write out custom error json."""
        data = {
            'code': status_code,
            'error': self._reason,
        }
        self.write(data)
        self.finish()

    def get_optional_argument(self, name: str, default: Any = None) -> Any:
        """Return argument, or default value if not present.

        Try from `self.request.body` first, then from
        `self.get_query_argument()`.
        """
        try:
            return self.get_required_argument(name)
        except tornado.web.HTTPError:
            return default

    def get_required_argument(self, name: str) -> Any:
        """Return argument, raise 400 if not present.

        Try from `self.request.body` first, then from
        `self.get_query_argument()`.
        """
        if self.request.body:
            try:
                return json_decode(self.request.body)[name]
            except KeyError:
                pass
        try:
            return self.get_query_argument(name)
        except tornado.web.MissingArgumentError:
            pass
        # fall-through
        raise tornado.web.HTTPError(400, reason=f"missing argument ({name})")


def authenticated(method):
    """
    Decorate methods with this to require that the Authorization
    header is filled with a valid token. Does *not* check the
    authorization of the token, just that it exists.

    On failure, raises a 403 error.

    Raises:
        :py:class:`tornado.web.HTTPError`
    """
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        if not self.current_user:
            raise tornado.web.HTTPError(403, reason="authentication failed")
        return await method(self, *args, **kwargs)
    return wrapper

def catch_error(method):
    """
    Decorator to catch and handle errors on handlers.

    All failures caught here 
    """
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        try:
            return await method(self, *args, **kwargs)
        except tornado.web.HTTPError:
            raise # tornado can handle this
        except tornado.httpclient.HTTPError:
            raise # tornado can handle this
        except Exception as e:
            logger.warning('Error in website handler', exc_info=True)
            try:
                self.statsd.incr(self.__class__.__name__+'.error')
            except Exception:
                pass
            message = 'Error in '+self.__class__.__name__
            self.send_error(500, reason=message)
    return wrapper

def role_authorization(**_auth):
    """
    Handle RBAC authorization.

    Like :py:func:`authenticated`, this requires the Authorization header
    to be filled with a valid token.  Note that calling both decorators
    is not necessary, as this decorator will perform authentication
    checking as well.

    Args:
        roles (list): The roles to match

    Raises:
        :py:class:`tornado.web.HTTPError`
    """
    def make_wrapper(method):
        @authenticated
        @catch_error
        @wraps(method)
        async def wrapper(self, *args, **kwargs):
            roles = _auth.get('roles', [])

            authorized = False

            auth_role = self.auth_data.get('role',None)
            if roles and auth_role in roles:
                authorized = True
            else:
                logger.info('roles: %r', roles)
                logger.info('token_role: %r', auth_role)
                logger.info('role mismatch')

            if not authorized:
                raise tornado.web.HTTPError(403, reason="authorization failed")

            return await method(self, *args, **kwargs)
        return wrapper
    return make_wrapper

def scope_role_auth(**_auth):
    """
    Handle RBAC authorization using oauth2 scopes.

    Like :py:func:`authenticated`, this requires the Authorization header
    to be filled with a valid token.  Note that calling both decorators
    is not necessary, as this decorator will perform authentication
    checking as well.

    Args:
        roles (list): The roles to match
        prefix (str): The scope prefix

    Raises:
        :py:class:`tornado.web.HTTPError`
    """
    def make_wrapper(method):
        @authenticated
        @catch_error
        @wraps(method)
        async def wrapper(self, *args, **kwargs):
            roles = _auth.get('roles', [])
            scope_prefix = _auth.get('prefix', None)

            authorized = False

            auth_roles = []
            for scope in self.auth_data.get('scope', '').split():
                if scope_prefix and scope.startswith(f'{scope_prefix}:'):
                    auth_roles.append(scope.split(':', 1)[-1])
            if roles and any(r in roles for r in auth_roles):
                authorized = True
            else:
                logging.info('roles: %r', roles)
                logging.info('token_roles: %r', auth_roles)
                logging.info('role mismatch')

            if not authorized:
                raise tornado.web.HTTPError(403, reason="authorization failed")

            return await method(self, *args, **kwargs)
        return wrapper
    return make_wrapper
