"""Handle argument parsing, defaulting, and casting."""


import argparse
import json
import re
from itertools import chain
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

import tornado.web
from tornado.escape import to_unicode
from wipac_dev_tools import strtobool

from ..utils.json_util import json_decode

T = TypeVar("T")


class _NoDefaultValue:  # pylint: disable=R0903
    """Signal no default value, AKA argument is required."""


NO_DEFAULT = _NoDefaultValue()


def _parse_json_body_arguments(request_body: bytes) -> Dict[str, Any]:
    """Return the request-body JSON-decoded, but only if it's a `dict`."""
    json_body = json_decode(request_body)

    if isinstance(json_body, dict):
        return cast(Dict[str, Any], json_body)
    return {}


class _InvalidArgumentError(Exception):
    """Raise when an argument-validation fails."""


def _make_400_error(arg_name: str, error: Exception) -> tornado.web.HTTPError:
    if isinstance(error, tornado.web.MissingArgumentError):
        error.reason = (
            f"`{arg_name}`: (MissingArgumentError) required argument is missing"
        )
        error.log_message = ""
        return error
    else:
        return tornado.web.HTTPError(400, reason=f"`{arg_name}`: {error}")


class ArgumentHandler(argparse.ArgumentParser):
    """Helper class for argument parsing, defaulting, and casting.

    Like argparse.ArgumentParser, but for REST & JSON-body arguments.
    """

    def __init__(self, source: dict[str, Any] | bytes) -> None:
        super().__init__(exit_on_error=False)
        self.source = source

    def add_argument(self, name: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """explain."""
        super().add_argument(f"--{name}", *args, **kwargs)

    def parse_args(self) -> argparse.Namespace:  # type: ignore[override]
        """Get the args -- like argparse.parse_args but parses a dict."""
        if isinstance(self.source, bytes):
            args_dict: dict[str, Any] = json.loads(self.source)
        else:
            args_dict = {
                k: " ".join(to_unicode(v) for v in vlist)
                for k, vlist in self.source.items()
            }

        # TODO - does putting in values verbatim work? or do we need to filter primitive_types
        args_tuples = [(f"--{k}", v) for k, v in args_dict.items()]
        arg_strings = list(chain.from_iterable(args_tuples))

        return super().parse_args(args=arg_strings)
