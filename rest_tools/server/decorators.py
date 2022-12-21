
from functools import wraps
import logging
import re

import tornado.web

from .. import telemetry as wtt

logger = logging.getLogger('auth_decorators')


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
                pass  # ignore statsd errors
            message = 'Error in '+self.__class__.__name__
            self.send_error(500, reason=message)
        return None
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

            auth_role = self.auth_data.get('role',None)
            if roles and auth_role in roles:
                wtt.set_current_span_attribute('self.auth_data.roles', auth_role)
            else:
                logger.info('roles: %r', roles)
                logger.info('token_role: %r', auth_role)
                logger.info('role mismatch')
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

            authorized = set(roles).intersection(auth_roles)

            if not authorized:
                logging.info('roles: %r', roles)
                logging.info('token_roles: %r', auth_roles)
                logging.info('role mismatch')
                raise tornado.web.HTTPError(403, reason="authorization failed")

            wtt.set_current_span_attribute('self.auth_data.roles', ','.join(sorted(authorized)))

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

            wtt.set_current_span_attribute('self.auth_data.roles', ','.join(sorted(authorized)))

            return await method(self, *args, **kwargs)
        return wrapper
    return make_wrapper


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

        logger.debug('token_val = %r', token_val)
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
                    logging.warning('exception in role auth', exc_info=True)
                    raise tornado.web.HTTPError(500, reason="internal server error") from exc

                if not authorized_roles:
                    logging.debug('roles requested: %r', roles)
                    logging.debug('role mismatch')
                    raise tornado.web.HTTPError(403, reason="authorization failed")

                logging.debug('roles requested: %r', roles)
                authorized_roles = sorted(authorized_roles)
                logging.debug('roles authorized: %r', authorized_roles)
                wtt.set_current_span_attribute('self.auth_data.roles', ','.join(authorized_roles))
                self.auth_roles = authorized_roles

                try:
                    authorized_groups = set()
                    for name in group_attrs:
                        for expression in group_attrs[name]:
                            ret = eval_expression(self.auth_data, expression)
                            authorized_groups.update(match.expand(name) for match in ret)
                except Exception as exc:
                    logging.warning('exception in group auth', exc_info=True)
                    raise tornado.web.HTTPError(500, reason="internal server error") from exc

                if authorized_groups:
                    authorized_groups = sorted(authorized_groups)
                    logging.debug('groups authorized: %r', authorized_groups)
                    wtt.set_current_span_attribute('self.auth_data.groups', ','.join(authorized_groups))
                    self.auth_groups = authorized_groups

                return await method(self, *args, **kwargs)
            return wrapper
        return make_wrapper
    return make_decorator
