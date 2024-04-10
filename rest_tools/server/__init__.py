"""Sub-package __init__."""

from .arghandler import ArgumentHandler, ArgumentSource
from .decorators import (
    authenticated,
    catch_error,
    keycloak_role_auth,
    role_authorization,
    scope_role_auth,
    token_attribute_role_mapping_auth,
    validate_request,
)
from .handler import (
    KeycloakUsernameMixin,
    OpenIDCookieHandlerMixin,
    OpenIDLoginHandler,
    RestHandler,
    RestHandlerSetup,
)
from .server import RestServer

__all__ = [
    "RestServer",
    "RestHandlerSetup",
    "RestHandler",
    "KeycloakUsernameMixin",
    "OpenIDCookieHandlerMixin",
    "OpenIDLoginHandler",
    "authenticated",
    "catch_error",
    "role_authorization",
    "scope_role_auth",
    "keycloak_role_auth",
    "token_attribute_role_mapping_auth",
    "ArgumentHandler",
    "ArgumentSource",
    "validate_request",
]
