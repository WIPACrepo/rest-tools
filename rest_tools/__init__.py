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
