"""RestHandler and related classes."""

# fmt:off
# pylint: skip-file

import base64
import hashlib
import hmac
import logging
import secrets
import time
import urllib.parse
from collections import defaultdict
from functools import partial, wraps
from typing import Any, Dict, List, MutableMapping, Optional, Type, TypeVar, Union

import rest_tools
import tornado.escape
import tornado.gen
import tornado.httpclient
import tornado.httputil
import tornado.web
from cachetools import TTLCache
from tornado.auth import OAuth2Mixin

from .. import telemetry as wtt
from ..utils.auth import Auth, OpenIDAuth
from . import arghandler
from .stats import RouteStats

T = TypeVar("T")


logger = logging.getLogger('rest')


def RestHandlerSetup(config={}):
    """Default RestHandler setup. Returns the default arguments for passing to
    the route setup.

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
        kwargs = {}
        if 'audience' in config['auth']:
            kwargs['audience'] = config['auth']['audience']
        if 'issuers' in config['auth']:
            kwargs['issuers'] = config['auth']['issuers']
        if 'secret' in config['auth']:
            kwargs['secret'] = config['auth']['secret']
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
            if 'algorithms' in config['auth']:
                kwargs['algorithms'] = config['auth']['algorithms']
            auth = OpenIDAuth(config['auth']['openid_url'], **kwargs)
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
    """Default REST handler."""
    def __init__(self, *args, **kwargs) -> None:
        self.server_header = ''
        try:
            super().__init__(*args, **kwargs)
        except Exception:
            logging.error('error', exc_info=True)

    def initialize(self, debug=False, auth=None, auth_url=None, module_auth_key='', server_header='', route_stats=None, **kwargs):
        super().initialize(**kwargs)
        self.debug = debug
        self.auth = auth
        self.auth_url = auth_url
        self.auth_data = {}
        self.auth_key = None
        self.module_auth_key = module_auth_key
        self.server_header = server_header
        self.route_stats = route_stats

    @wtt.spanned(
        span_namer=wtt.SpanNamer(use_this_arg='self.request.method'),
        kind=wtt.SpanKind.SERVER,
        these=["self.request.method", "self.request.path"],
        carrier="self.request.headers",
    )
    async def _execute(self, *args: Any, **kwargs: Any) -> None:
        """Call implemented methods.

        NOTE: This is the closest common call-stack ancestor of
            - `prepare()`,
            - "method handlers" (`get()`, `post()`, ...),
            - `on_finish()`,
            - etc.
        """
        return await super()._execute(*args, **kwargs)

    def set_default_headers(self):
        self._headers['Server'] = self.server_header

    def get_template_namespace(self):
        namespace = super().get_template_namespace()
        namespace['version'] = rest_tools.__version__
        return namespace

    def get_current_user(self):
        """Get the current user, and set auth-related attributes."""
        try:
            type, token = self.request.headers['Authorization'].split(' ', 1)
            if type.lower() != 'bearer':
                raise Exception('bad header type')
            logger.debug('token: %r', token)
            data = self.auth.validate(token)
            self.auth_data = data
            self.auth_key = token
            if "role" in self.auth_data:
                wtt.set_current_span_attribute('self.auth_data.role', self.auth_data['role'])
            return data['sub']
        # Auth Failed
        except Exception:
            if self.debug and 'Authorization' in self.request.headers:
                logger.info('Authorization: %r', self.request.headers['Authorization'])
            logger.info('failed auth', exc_info=True)

        return None

    @wtt.evented()
    def prepare(self):
        """Prepare before http-method request handlers."""
        if self.route_stats is not None:
            stat = self.route_stats[self.request.path]
            if stat.is_overloaded():
                backoff = stat.get_backoff_time()
                logger.warn('Server is overloaded, backoff %r', backoff)
                self.set_header('Retry-After', backoff)
                raise tornado.web.HTTPError(503, reason="server overloaded")
            self.start_time = time.time()

    @wtt.evented()
    def on_finish(self):
        """Cleanup after http-method request handlers."""
        if self.route_stats is not None and self.get_status() < 500:
            stat = self.route_stats[self.request.path]
            stat.append(time.time() - self.start_time)

    @wtt.evented(all_args=True)
    def write_error(self, status_code=500, **kwargs):
        """Write out custom error json."""
        data = {
            'code': status_code,
            'error': self._reason,
        }
        self.write(data)
        self.finish()

    def get_json_body_argument(
        self,
        name: str,
        default: Any = arghandler.NO_DEFAULT,
        type: Optional[Type[T]] = None,
        choices: Optional[List[Any]] = None,
        forbiddens: Optional[List[Any]] = None,
    ) -> T:
        """Get argument from the JSON-decoded request-body.

        If no `default` is provided, and the argument is not present, raise `400`.

        Arguments:
            name -- the argument's name

        Keyword Arguments:
            default -- a default value to use if the argument is not present
            type -- optionally, typecast the argument's value (raise `400` for invalid value)
            choices -- a list of valid argument values (raise `400`, if arg's value is not in list)
            forbiddens -- a list of disallowed argument values (raise `400`, if arg's value is in list)

        Returns:
            the argument's value, possibly stripped/typecasted
        """
        return arghandler.ArgumentHandler.get_json_body_argument(
            self.request.body, name, default, type, choices, forbiddens
        )

    def get_argument(
        self,
        name: str,
        default: Any = arghandler.NO_DEFAULT,
        strip: bool = True,
        type: Optional[Type[T]] = None,
        choices: Optional[List[Any]] = None,
        forbiddens: Optional[List[Any]] = None,
    ) -> T:
        """Get argument from query base-arguments / JSON-decoded request-body.

        If no `default` is provided, and the argument is not present, raise `400`.

        Arguments:
            name -- the argument's name

        Keyword Arguments:
            default -- a default value to use if the argument is not present
            strip {`bool`} -- whether to `str.strip()` the arg's value (default: {`True`})
            type -- optionally, typecast the argument's value (raise `400` for invalid value)
            choices -- a list of valid argument values (raise `400`, if arg's value is not in list)
            forbiddens -- a list of disallowed argument values (raise `400`, if arg's value is in list)

        Returns:
            the argument's value, possibly stripped/typecasted
        """
        return arghandler.ArgumentHandler.get_argument(
            self.request.body, super().get_argument, name, default, strip, type, choices, forbiddens
        )


def authenticated(method):
    """Decorate methods with this to require that the Authorization header is
    filled with a valid token. Does *not* check the authorization of the token,
    just that it exists.

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
    """Decorator to catch and handle errors on handlers.

    All failures caught here
    """
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        try:
            return await method(self, *args, **kwargs)
        except tornado.web.HTTPError:
            raise  # tornado can handle this
        except tornado.httpclient.HTTPError:
            raise  # tornado can handle this
        except Exception:
            logger.warning('Error in website handler', exc_info=True)
            try:
                self.statsd.incr(self.__class__.__name__+'.error')
            except Exception:
                pass
            message = 'Error in '+self.__class__.__name__
            self.send_error(500, reason=message)
    return wrapper


def role_authorization(**_auth):
    """Handle RBAC authorization.

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
    """Handle RBAC authorization using oauth2 scopes.

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


def keycloak_role_auth(**_auth):
    """Handle RBAC authorization using keycloak realm roles.
    Like :py:func:`authenticated`, this requires the Authorization header
    to be filled with a valid token.  Note that calling both decorators
    is not necessary, as this decorator will perform authentication
    checking as well.

    Args:
        roles (list): The roles to match
        prefix (str): The token prefix (default: realm_access.roles)
    Raises:
        :py:class:`tornado.web.HTTPError`
    """
    def make_wrapper(method):
        @authenticated
        @catch_error
        @wraps(method)
        async def wrapper(self, *args, **kwargs):
            roles = _auth.get('roles', [])
            prefix = _auth.get('prefix', 'realm_access.roles').split('.')

            auth_roles = self.auth_data
            while prefix:
                auth_roles = auth_roles.get(prefix[0], {})
                prefix = prefix[1:]

            authorized = set(roles).intersection(auth_roles)

            if not authorized:
                logging.info('roles: %r', roles)
                logging.info('token_roles: %r', auth_roles)
                logging.info('role mismatch')
                raise tornado.web.HTTPError(403, reason="authorization failed")

            return await method(self, *args, **kwargs)
        return wrapper
    return make_wrapper


class OpenIDLoginHandler(RestHandler, OAuth2Mixin):
    """
    Handle OpenID Connect logins.

    Requires the `login_url` application setting to be a full url.
    """
    _pkcs_challenges: MutableMapping[str, str] = TTLCache(maxsize=10000, ttl=3600)

    def initialize(self, oauth_client_id, oauth_client_secret, oauth_client_scope=None, **kwargs):
        super().initialize(**kwargs)
        if not isinstance(self.auth, OpenIDAuth):
            raise RuntimeError('OpenID Connect auth not set up')
        self._OAUTH_AUTHORIZE_URL = self.auth.provider_info['authorization_endpoint']
        self._OAUTH_ACCESS_TOKEN_URL = self.auth.provider_info['token_endpoint']
        self._OAUTH_LOGOUT_URL = self.auth.provider_info['end_session_endpoint']
        self._OAUTH_USERINFO_URL = self.auth.provider_info['userinfo_endpoint']
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret
        if oauth_client_scope:
            self.oauth_client_scope = oauth_client_scope.split()
        else:
            self.oauth_client_scope = ['profile', 'groups']
            if oauth_client_secret:
                self.oauth_client_scope.append('offline_access')

    @classmethod
    def create_pkce_challenge(cls) -> str:
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').split('=')[0]
        cls._pkcs_challenges[code_challenge] = code_verifier
        return code_challenge

    @classmethod
    def get_pkce_verifier(cls, challenge: str) -> str:
        if challenge in cls._pkcs_challenges:
            return cls._pkcs_challenges[challenge]
        raise KeyError('invalid pkce challenge')

    async def get_authenticated_user(
        self, redirect_uri: str, code: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        http = self.get_auth_http_client()
        body = {
            'redirect_uri': redirect_uri,
            'code': code,
            'client_id': self.oauth_client_id,
            'grant_type': 'authorization_code',
        }
        if self.oauth_client_secret:
            body['client_secret'] = self.oauth_client_secret
        else:
            # use PKCE
            code_challenge = state.get('code_challenge', None)
            if not code_challenge:
                raise tornado.web.HTTPError(400, reason='missing PKCE code challenge')
            body['code_verifier'] = self.get_pkce_verifier(code_challenge)

        response = await http.fetch(
            self._OAUTH_ACCESS_TOKEN_URL,
            method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body=urllib.parse.urlencode(body),
        )
        ret = tornado.escape.json_decode(response.body)
        if not ret.get('id_token', ''):
            response = await http.fetch(
                self._OAUTH_USERINFO_URL,
                method='GET',
                headers={'Authorization': f'Bearer {ret["access_token"]}'},
            )
            ret['id_token'] = tornado.escape.json_decode(response.body)

        try:
            self.auth.validate(ret['access_token'])
        except Exception:
            if self.debug:
                logger.debug(f'bad token: {ret}')
            raise
        return ret

    def _decode_state(self, state: Union[bytes, str]) -> str:
        data = tornado.escape.json_decode(base64.b64decode(state))
        _, token, _ = self._decode_xsrf_token(data.pop('xsrf'))
        _, expected_token, _ = self._get_raw_xsrf_token()
        if not token:
            raise tornado.web.HTTPError(403, reason="'state' argument has invalid format")
        if not hmac.compare_digest(tornado.escape.utf8(token), tornado.escape.utf8(expected_token)):
            raise tornado.web.HTTPError(403, reason="XSRF cookie does not match state argument")
        return data

    def _encode_state(self, data: Dict[str, Any]) -> bytes:
        data2 = data.copy()  # make a copy to not add xsrf to source dict
        data2['xsrf'] = self.xsrf_token.decode('utf-8')
        return base64.b64encode(tornado.escape.json_encode(data2).encode('utf-8'))

    @catch_error
    async def get(self):
        if self.get_argument('error', False):
            err = self.get_argument('error_description', None)
            if not err:
                err = 'unknown oauth2 error'
            raise tornado.web.HTTPError(400, reason=err)
        elif self.get_argument('code', False):
            data = self._decode_state(self.get_argument('state'))
            user = await self.get_authenticated_user(
                redirect_uri=self.get_login_url(),
                code=self.get_argument('code'),
                state=data,
            )

            # set expire times (can be 0 in user data, which is an invalid cookie)
            access_expire = user.get('expires_in', 0)
            if not access_expire:
                access_expire = 1800
            refresh_expire = user.get('refresh_expires_in', 0)
            if not refresh_expire:
                refresh_expire = 86400

            # Save the user with e.g. set_secure_cookie
            self.set_secure_cookie('access_token', user['access_token'],
                                   expires_days=float(access_expire)/3600/24)
            if 'refresh_token' in user:
                self.set_secure_cookie('refresh_token', user['refresh_token'],
                                       expires_days=float(refresh_expire)/3600/24)
            self.set_secure_cookie('identity', tornado.escape.json_encode(user['id_token']),
                                   expires_days=float(refresh_expire)/3600/24)
            if data.get('redirect', None):
                url = data['redirect']
                if 'state' in data:
                    url = tornado.httputil.url_concact(url, {'state': data['state']})
                self.redirect(url)
            elif self.settings.get('debug', False):
                self.write(user)
            else:
                raise tornado.web.HTTPError(400, reason='missing redirect')
        else:
            state = {}
            redirect = self.get_argument('next', None)
            if not redirect:
                redirect = self.get_argument('redirect', None)
            if redirect:
                state['redirect'] = redirect
            elif not self.settings.get('debug', False):
                raise tornado.web.HTTPError(400, 'missing redirect')
            if self.get_argument('state', False):
                state['state'] = self.get_argument('state')
            extra_params = {}
            if not self.oauth_client_secret:
                # use PKCE  https://www.rfc-editor.org/rfc/rfc7636
                extra_params['code_challenge'] = self.create_pkce_challenge()
                extra_params['code_challenge_method'] = 'S256'
                state['code_challenge'] = extra_params['code_challenge']
            extra_params["state"] = self._encode_state(state)

            self.authorize_redirect(
                redirect_uri=self.get_login_url(),
                client_id=self.oauth_client_id,
                scope=self.oauth_client_scope,
                extra_params=extra_params,
                response_type='code')
