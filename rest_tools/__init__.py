# version is a human-readable version number.

from . import client, server, utils

from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("wipac-rest-tools")
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = [
    "client",
    "server",
    "utils",
]

# NOTE: `__version__` is not defined because this package is built using 'setuptools-scm' --
#   use `importlib.metadata.version(...)` if you need to access version info at runtime.
