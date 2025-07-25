"""RestHandler and related classes."""

import base64
from collections.abc import Callable, Awaitable
import functools
import hmac
from inspect import isawaitable
import json
import logging
import time
import urllib.parse
from collections import defaultdict
from typing import Any, Dict, Optional, Union

import tornado.escape
import tornado.gen
import tornado.httpclient
import tornado.httputil
import tornado.web
from tornado.auth import OAuth2Mixin

import rest_tools
from .decorators import catch_error
from .stats import RouteStats
from .. import telemetry as wtt
from ..utils.auth import Auth, OpenIDAuth
from ..utils.json_util import json_decode
from ..utils.pkce import PKCEMixin

LOGGER = logging.getLogger(__name__)


# fmt:off


def _log_auth_failed(e: Exception):
    LOGGER.info('failed auth')
    if LOGGER.isEnabledFor(logging.DEBUG):
        LOGGER.exception(e)


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
        if 'leeway' in config['auth']:
            kwargs['leeway'] = config['auth']['leeway']
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
        route_stats = defaultdict(functools.partial(RouteStats, **config['route_stats']))
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
            LOGGER.error('error', exc_info=True)

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
            LOGGER.debug('token: %r', token)
            data = self.auth.validate(token)
            self.auth_data = data
            self.auth_key = token
            return data['sub']
        # Auth Failed
        except Exception as e:
            if self.debug and 'Authorization' in self.request.headers:
                LOGGER.info('Authorization: %r', self.request.headers['Authorization'])
            _log_auth_failed(e)

        return None

    @wtt.evented()
    def prepare(self):
        """Prepare before http-method request handlers."""

        # log at the very start of every new request
        logging.info(">>> %s", self._request_summary())  # use the root logger
        # ^^^ this mimics the log line that tornado provides at the end of a request:
        #       see rest_tools.server.tornado_logger().
        #       ">>>" makes logs line-up (end-of-request log line uses http code: 200, 400, etc.)
        LOGGER.debug(f"[{self.__class__.__name__}]")

        if self.route_stats is not None:
            stat = self.route_stats[self.request.path]
            if stat.is_overloaded():
                backoff = stat.get_backoff_time()
                LOGGER.warning('Server is overloaded, backoff %r', backoff)
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

    @functools.cached_property
    def json_body_arguments(self) -> Dict[str,Any]:
        """Get the body arguments, decoded from a JSON-encoded request body."""
        if not self.request.body:
            return {}

        try:
            args = json_decode(self.request.body)
        except json.JSONDecodeError:
            raise tornado.web.HTTPError(
                400, reason="requests body is not JSON-encoded"
            )

        if not isinstance(args, dict):
            raise tornado.web.HTTPError(
                400, reason="JSON-encoded requests body must be a 'dict'"
            )
        return args

    def get_argument(
        self,
        name: str,
        default: Any = tornado.web._ARG_DEFAULT,
        strip: bool = True,
        # deprecated args
        type: Any = None,
        choices: Any = None,
        forbiddens: Any = None,
        strict_type: Any = None,
    ) -> Any:
        """Get argument from query base-arguments / JSON-decoded request-body.

        If no `default` is provided, and the argument is not present, raise `400`.

        Arguments:
            name -- the argument's name

        Keyword Arguments:
            default -- a default value to use if the argument is not present
            strip {`bool`} -- whether to `str.strip()` the arg's value (default: {`True`})
            type -- **deprecated**
            choices -- **deprecated**
            forbiddens -- **deprecated**
            strict_type -- **deprecated**

        Returns:
            the argument's value, possibly stripped
        """
        if type is not None or choices is not None or forbiddens is not None or strict_type is not None:
            raise RuntimeError("advanced argument checking is deprecated, please use ArgumentHandler instead")

        # 1st: check query args w/o default
        try:
            return super().get_argument(name, strip=strip)  # no default
        except tornado.web.MissingArgumentError:
            pass

        # 2nd: check json-body args w/o default
        try:
            return self.json_body_arguments[name]  # no default
        except KeyError:
            pass

        # Finally: check json-body args w/ default
        return super().get_argument(name, default, strip=strip)


class KeycloakUsernameMixin:
    """Get the username correctly from Keycloak tokens.

    Note: will not work on service account tokens.
    """
    def get_current_user(self):
        if not super().get_current_user():
            return None
        username = self.auth_data.get('preferred_username', None)
        if not username:
            username = self.auth_data.get('upn', None)
            if not username:
                LOGGER.info('could not find auth username')
        return username


class OpenIDCookieHandlerMixin:
    """Store/load current user's `OpenIDLoginHandler` tokens in cookies."""
    auth: OpenIDAuth
    get_secure_cookie: Callable[..., Optional[bytes]]
    set_secure_cookie: Callable[..., None]
    clear_cookie: Callable[..., None]

    def get_current_user(self) -> Union[str, None]:
        """Get the current user, and set auth-related attributes."""
        try:
            access_token = self.get_secure_cookie('access_token')
            data = self.auth.validate(access_token)
            self.auth_data = data
            self.auth_key = access_token
            refresh_token = self.get_secure_cookie('refresh_token')
            self.auth_refresh_token = refresh_token
            return data['sub']
        # Auth Failed
        except Exception as e:
            _log_auth_failed(e)
        return None

    def store_tokens(
        self,
        access_token,
        access_token_exp,
        refresh_token=None,
        refresh_token_exp=None,
        user_info=None,
        user_info_exp=None,
    ) -> Union[None, Awaitable[None]]:
        """Store jwt tokens and user info from OpenID-compliant auth source.

        Args:
            access_token (str): jwt access token
            access_token_exp (int): access token expiration in seconds
            refresh_token (str): jwt refresh token
            refresh_token_exp (int): refresh token expiration in seconds
            user_info (dict): user info (from id token or user info lookup)
            user_info_exp (int): user info expiration in seconds
        """
        self.set_secure_cookie('access_token', access_token,
                               expires_days=float(access_token_exp)/3600/24)
        if refresh_token and refresh_token_exp:
            self.set_secure_cookie('refresh_token', refresh_token,
                                   expires_days=float(refresh_token_exp)/3600/24)
        if user_info and user_info_exp:
            self.set_secure_cookie('user_info', tornado.escape.json_encode(user_info),
                                   expires_days=float(user_info_exp)/3600/24)
        return None

    def clear_tokens(self):
        """Clear token data, usually on logout."""
        self.clear_cookie('access_token')
        self.clear_cookie('refresh_token')
        self.clear_cookie('user_info')


class OpenIDLoginHandler(OpenIDCookieHandlerMixin, OAuth2Mixin, PKCEMixin, RestHandler):
    """Handle OpenID Connect logins.

    Should be combined with an appropriate mixin to store the token(s).
    `OpenIDCookieHandlerMixin` is used by default, but can be overridden.

    Requires the `login_url` application setting to be a full url.
    """
    store_tokens: Callable[..., Awaitable[None]]

    def initialize(self, oauth_client_id, oauth_client_secret, oauth_client_scope=None, **kwargs):  # type: ignore
        super().initialize(**kwargs)
        if not isinstance(self.auth, OpenIDAuth):
            raise RuntimeError('OpenID Connect auth not set up')
        self._OAUTH_AUTHORIZE_URL = self.auth.provider_info['authorization_endpoint']
        self._OAUTH_ACCESS_TOKEN_URL = self.auth.provider_info['token_endpoint']
        self._OAUTH_LOGOUT_URL = self.auth.provider_info['end_session_endpoint']
        self._OAUTH_USERINFO_URL = self.auth.provider_info['userinfo_endpoint']
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret

        scopes = {'openid', 'profile'}
        if oauth_client_scope is not None:
            scopes.update(oauth_client_scope.split())
        else:
            scopes.add('groups')
        if oauth_client_secret:
            scopes.add('offline_access')
        self.oauth_client_scope = list(scopes)

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
        kwargs = {}
        if self.oauth_client_secret:
            kwargs['auth_username'] = self.oauth_client_id
            kwargs['auth_password'] = self.oauth_client_secret
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
            **kwargs,
        )
        ret = tornado.escape.json_decode(response.body)
        if not ret.get('id_token', ''):
            response = await http.fetch(
                self._OAUTH_USERINFO_URL,
                method='GET',
                headers={'Authorization': f'Bearer {ret["access_token"]}'},
            )
            ret['id_token'] = tornado.escape.json_decode(response.body)

        if ret.get('id_token') and isinstance(ret['id_token'], str):
            ret['id_token'] = self.auth.validate(ret['id_token'])

        try:
            self.auth.validate(ret['access_token'])
        except Exception:
            if self.debug:
                LOGGER.debug(f'bad token: {ret}')
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

            # Save the user data
            ret = self.store_tokens(
                access_token=user['access_token'],
                access_token_exp=access_expire,
                refresh_token=user.get('refresh_token'),
                refresh_token_exp=refresh_expire,
                user_info=user.get('id_token'),
                user_info_exp=refresh_expire if user.get('refresh_token') else access_expire,
            )
            if ret and isawaitable(ret):
                await ret

            if data.get('redirect', None):
                url = data['redirect']
                if 'state' in data:
                    url = tornado.httputil.url_concat(url, {'state': data['state']})
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
