"""Sub-package __init__."""


from .handler import (
    RestHandler,
    RestHandlerSetup,
    OpenIDLoginHandler,
    authenticated,
    catch_error,
    role_authorization,
    scope_role_auth,
)
from .server import RestServer

__all__ = [
    "RestServer",
    "RestHandlerSetup",
    "RestHandler",
    "OpenIDLoginHandler",
    "authenticated",
    "catch_error",
    "role_authorization",
    "scope_role_auth",
]
