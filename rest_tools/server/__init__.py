"""Sub-package __init__."""


from .handler import (
    RestHandler,
    RestHandlerSetup,
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
    "authenticated",
    "catch_error",
    "role_authorization",
    "scope_role_auth",
]
