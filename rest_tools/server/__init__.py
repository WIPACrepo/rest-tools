"""Sub-package __init__."""

from .arghandler import ArgumentHandler, ArgumentSource
from .decorators import (
    TokenAttributeRoleMappingProtocol,
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
    "ArgumentHandler",
    "ArgumentSource",
    "KeycloakUsernameMixin",
    "OpenIDCookieHandlerMixin",
    "OpenIDLoginHandler",
    "RestHandler",
    "RestHandlerSetup",
    "RestServer",
    "TokenAttributeRoleMappingProtocol",
    "authenticated",
    "catch_error",
    "keycloak_role_auth",
    "role_authorization",
    "scope_role_auth",
    "token_attribute_role_mapping_auth",
    "validate_request",
]
