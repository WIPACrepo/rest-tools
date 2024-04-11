"""decorators.py."""

# fmt:off

import logging
import os
import re
from functools import wraps
from inspect import isawaitable

import requests.exceptions
import tornado.web

from .. import telemetry as wtt

LOGGER = logging.getLogger(__name__)


########################################################################################################################


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
        ret = method(self, *args, **kwargs)
        if isawaitable(ret):
            return await ret
        else:
            return ret
    return wrapper


########################################################################################################################


def catch_error(method):
    """Decorator to catch and handle errors on handlers.

    All failures caught here
    """
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        try:
            ret = method(self, *args, **kwargs)
            if isawaitable(ret):
                return await ret
            else:
                return ret
        except tornado.web.HTTPError:
            raise  # tornado can handle this
        except tornado.httpclient.HTTPError:
            raise  # tornado can handle this
        except requests.exceptions.HTTPError as e:
            LOGGER.warning('Error in website handler', exc_info=True)
            try:
                self.statsd.incr(self.__class__.__name__+'.error')
            except Exception:
                pass  # ignore statsd errors
            if e.response.status_code == 403:
                code = 403
                message = 'Error authenticating user'
            else:
                code = 500
                message = 'Error contacting backend in '+self.__class__.__name__
            self.send_error(code, reason=message)
        except Exception:
            LOGGER.warning('Error in website handler', exc_info=True)
            try:
                self.statsd.incr(self.__class__.__name__+'.error')
            except Exception:
                pass  # ignore statsd errors
            message = 'Error in '+self.__class__.__name__
            self.send_error(500, reason=message)
        return None
    return wrapper


########################################################################################################################


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

            auth_role = self.auth_data.get('role',None)
            if roles and auth_role in roles:
                wtt.set_current_span_attribute('self.auth_data.roles', auth_role)
            else:
                LOGGER.info('roles: %r', roles)
                LOGGER.info('token_role: %r', auth_role)
                LOGGER.info('role mismatch')
                raise tornado.web.HTTPError(403, reason="authorization failed")

            ret = method(self, *args, **kwargs)
            if isawaitable(ret):
                return await ret
            else:
                return ret
        return wrapper
    return make_wrapper


########################################################################################################################


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

            authorized = set(roles).intersection(auth_roles)

            if not authorized:
                LOGGER.info('roles: %r', roles)
                LOGGER.info('token_roles: %r', auth_roles)
                LOGGER.info('role mismatch')
                raise tornado.web.HTTPError(403, reason="authorization failed")

            wtt.set_current_span_attribute('self.auth_data.roles', ','.join(sorted(authorized)))

            ret = method(self, *args, **kwargs)
            if isawaitable(ret):
                return await ret
            else:
                return ret
        return wrapper
    return make_wrapper


########################################################################################################################


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
                LOGGER.info('roles: %r', roles)
                LOGGER.info('token_roles: %r', auth_roles)
                LOGGER.info('role mismatch')
                raise tornado.web.HTTPError(403, reason="authorization failed")

            wtt.set_current_span_attribute('self.auth_data.roles', ','.join(sorted(authorized)))

            ret = method(self, *args, **kwargs)
            if isawaitable(ret):
                return await ret
            else:
                return ret
        return wrapper
    return make_wrapper


########################################################################################################################


def token_attribute_role_mapping_auth(role_attrs, group_attrs=None):
    """Handle RBAC authorization by creating a decorator that maps token
    attributes to roles, then using the decorator to allow access to functions
    by role.  Can also map groups and add that to auth data.

    Like :py:func:`authenticated`, this requires the Authorization header
    to be filled with a valid token.  Note that calling both decorators
    is not necessary, as this decorator will perform authentication
    checking as well.

    Use an attr expression for evaluating a role or group.  Some examples:
      * For an exact match on a string: `attr=foo`
      * For a list, the element must exist in the list: `my.attr=foo`
      * Scope is handled like a list, splitting the string on spaces

    Python regular expressions are supported on values, which can also be used
    to capture a value to use as the name of the role or group:
      * For matching any value: `my.attr=.*`
      * For capturing a value: `my.attr=(foo)`
      * For capturing part of a value: `my.attr=foo(.*)`
    Note that this uses `re.fullmatch`.

    Args:
        role_attrs (dict): Map of role name to list of valid attr expressions
        group_attrs (dict): Map of group name to list of valid attr expressions
    Returns:
        callable: Decorator function

    Decorator Args:
        roles (list): The roles to match
    Decorator Raises:
        :py:class:`tornado.web.HTTPError`

    Example:
        my_auth = token_attribute_role_mapping_auth(
            role_attrs = {
                'write': ['groups=my-service-write', 'groups=admins'],
                'read': ['groups'],
            },
            group_attrs = {
                r'\1': [r'groups=my-service-(.*)']
            }
        )

        class Handler:
            @my_auth(roles=['read', 'write'])
            async def get(self):
                pass
            @my_auth(roles['write'])
            async def post(self):
                pass
    """
    basic_role_attrs = set()
    regex_role_attrs = set()
    for name in role_attrs:
        if re.fullmatch(r'\w+', name):
            basic_role_attrs.add(name)
        else:
            regex_role_attrs.add(name)
    if not group_attrs:
        group_attrs = {}

    def eval_expression(token, e):
        name, val = e.split('=',1)
        if name == 'scope':
            # special handling to split into string
            token_val = token.get('scope','').split()
        else:
            prefix = name.split('.')[:-1]
            while prefix:
                token = token.get(prefix[0], {})
                prefix = prefix[1:]
            token_val = token.get(name.split('.')[-1], None)

        LOGGER.debug('token_val = %r', token_val)
        if token_val is None:
            return []

        prog = re.compile(val)
        if isinstance(token_val, list):
            ret = (prog.fullmatch(v) for v in token_val)
        else:
            ret = [prog.fullmatch(token_val)]
        return [r for r in ret if r]

    def make_decorator(**_auth):
        def make_wrapper(method):
            @authenticated
            @catch_error
            @wraps(method)
            async def wrapper(self, *args, **kwargs):
                roles = _auth.get('roles', [])

                try:
                    authorized_roles = set()
                    for role in basic_role_attrs.intersection(roles):
                        for expression in role_attrs[role]:
                            if eval_expression(self.auth_data, expression):
                                authorized_roles.add(role)
                    for name in regex_role_attrs:
                        for expression in role_attrs[name]:
                            ret = eval_expression(self.auth_data, expression)
                            rolenames = [match.expand(name) for match in ret]
                            authorized_roles.update(role for role in roles if role in rolenames)
                except Exception as exc:
                    LOGGER.warning('exception in role auth', exc_info=True)
                    raise tornado.web.HTTPError(500, reason="internal server error") from exc

                if not authorized_roles:
                    LOGGER.debug('roles requested: %r', roles)
                    LOGGER.debug('role mismatch')
                    raise tornado.web.HTTPError(403, reason="authorization failed")

                LOGGER.debug('roles requested: %r', roles)
                authorized_roles = sorted(authorized_roles)
                LOGGER.debug('roles authorized: %r', authorized_roles)
                wtt.set_current_span_attribute('self.auth_data.roles', ','.join(authorized_roles))
                self.auth_roles = authorized_roles

                try:
                    authorized_groups = set()
                    for name in group_attrs:
                        for expression in group_attrs[name]:
                            ret = eval_expression(self.auth_data, expression)
                            authorized_groups.update(match.expand(name) for match in ret)
                except Exception as exc:
                    LOGGER.warning('exception in group auth', exc_info=True)
                    raise tornado.web.HTTPError(500, reason="internal server error") from exc

                if authorized_groups:
                    authorized_groups = sorted(authorized_groups)
                    LOGGER.debug('groups authorized: %r', authorized_groups)
                    wtt.set_current_span_attribute('self.auth_data.groups', ','.join(authorized_groups))
                    self.auth_groups = authorized_groups

                ret = method(self, *args, **kwargs)
                if isawaitable(ret):
                    return await ret
                else:
                    return ret
            return wrapper
        return make_wrapper
    return make_decorator


########################################################################################################################
# fmt:on

try:
    import openapi_core
    from openapi_core import OpenAPI
    from openapi_core.contrib import requests as openapi_core_requests
    from openapi_core.validation.exceptions import ValidationError
except ImportError:
    pass  # if client code wants to use these features, then let the built-in errors raise


def validate_request(openapi_spec: "OpenAPI"):
    """Validate request obj against the given OpenAPI spec."""

    def make_wrapper(method):  # type: ignore[no-untyped-def]
        async def wrapper(zelf: tornado.web.RequestHandler, *args, **kwargs):  # type: ignore[no-untyped-def]
            LOGGER.info("validating with openapi spec")
            # NOTE - don't change data (unmarshal) b/c we are downstream of data separation
            try:
                # https://openapi-core.readthedocs.io/en/latest/validation.html
                openapi_spec.validate_request(
                    _http_server_request_to_openapi_request(zelf.request),
                )
            except ValidationError as e:
                LOGGER.error(f"invalid request: {e.__class__.__name__} - {e}")
                if isinstance(  # look at the ORIGINAL exception that caused this error
                    e.__context__,
                    openapi_core.validation.schemas.exceptions.InvalidSchemaValue,
                ):
                    reason = "; ".join(  # to client
                        # verbose details after newline
                        str(x).split("\n", maxsplit=1)[0]
                        for x in e.__context__.schema_errors
                    )
                else:
                    reason = str(e)  # to client
                if os.getenv("CI"):
                    # in prod, don't fill up logs w/ traces from invalid data
                    LOGGER.exception(e)
                raise tornado.web.HTTPError(
                    status_code=400,
                    log_message=f"{e.__class__.__name__}: {e}",  # to stderr
                    reason=reason,  # to client
                )
            except Exception as e:
                LOGGER.error(f"unexpected exception: {e.__class__.__name__} - {e}")
                LOGGER.exception(e)
                raise tornado.web.HTTPError(
                    status_code=400,
                    log_message=f"{e.__class__.__name__}: {e}",  # to stderr
                    reason=None,  # to client (don't send possibly sensitive info)
                )

            return await method(zelf, *args, **kwargs)

        return wrapper

    return make_wrapper


def _http_server_request_to_openapi_request(
    req: tornado.httputil.HTTPServerRequest,
) -> "openapi_core_requests.RequestsOpenAPIRequest":
    """Convert a `tornado.httputil.HTTPServerRequest` to openapi's type."""
    return openapi_core_requests.RequestsOpenAPIRequest(
        requests.Request(
            method=req.method.lower() if req.method else "get",
            url=f"{req.protocol}://{req.host}{req.uri}",
            headers=req.headers,
            files=req.files,
            data=req.body if not req.body_arguments else None,  # see below
            params=req.query_arguments,
            # auth=None,
            cookies=req.cookies,
            # hooks=None,
            json=req.body_arguments if req.body_arguments else None,  # see above
        )
    )


########################################################################################################################
