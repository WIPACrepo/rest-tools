"""Sub-package __init__."""

from .auth import Auth, OpenIDAuth
from .config import from_environment
from .daemon import Daemon
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
    "Auth",
    "OpenIDAuth",
    "Daemon",
    "from_environment",
]
