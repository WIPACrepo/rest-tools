"""Handle argument parsing, defaulting, and casting."""


import argparse
import contextlib
import enum
import io
import json
import logging
import re
import sys
import time
import traceback
from typing import Any, List, TypeVar, Union

import tornado.web
from tornado.escape import to_unicode
from wipac_dev_tools import strtobool

from ..utils.json_util import json_decode
from .handler import RestHandler

T = TypeVar("T")

LOGGER = logging.getLogger(__name__)


class ArgumentSource(enum.Enum):
    """For mapping to argument sources."""

    QUERY_ARGUMENTS = enum.auto()
    JSON_BODY_ARGUMENTS = enum.auto()


ARGUMENTS_REQUIRED_PATTERN = re.compile(
    r".+: error: (the following arguments are required: .+)"
)
UNRECOGNIZED_ARGUMENTS_PATTERN = re.compile(r".+ error: (unrecognized arguments:) (.+)")
INVALID_VALUE_PATTERN = re.compile(r"(argument .+: invalid) .+ value: '.+'")

USE_CACHED_VALUE_PLACEHOLDER = "PLACEHOLDER"


class ArgumentHandler:
    """Helper class for argument parsing, defaulting, and casting.

    Like argparse.ArgumentParser, but for REST & JSON-body arguments.
    """

    def __init__(
        self, argument_source: ArgumentSource, rest_handler: RestHandler
    ) -> None:
        if sys.version_info < (3, 9):
            # ArgumentParser's `exit_on_error` is only python 3.9+
            self._argparser: argparse.ArgumentParser  # mypy hack
            self.argument_source: ArgumentSource  # mypy hack
            self.rest_handler: RestHandler  # mypy hack
            raise RuntimeError(
                f"{self.__class__.__name__} is supported only for python 3.9+"
            )

        self._argparser = argparse.ArgumentParser(exit_on_error=False)
        self.argument_source = argument_source
        self.rest_handler = rest_handler

    def add_argument(
        self,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Add an argument -- like argparse.add_argument with additions.

        See https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
        """

        def retrieve_json_body_arg(parsed_val: Any) -> Any:
            if parsed_val != USE_CACHED_VALUE_PLACEHOLDER:
                raise RuntimeError(
                    f"json value should be '{USE_CACHED_VALUE_PLACEHOLDER}' not: {parsed_val}"
                )
            return self.rest_handler.json_body_arguments[name]

        if kwargs.get("type") == bool:
            kwargs["type"] = strtobool
        if self.argument_source == ArgumentSource.JSON_BODY_ARGUMENTS:
            if "type" in kwargs:
                typ = kwargs["type"]  # put in var to avoid unintended recursion
                kwargs["type"] = lambda x: typ(retrieve_json_body_arg(x))
            else:
                kwargs["type"] = retrieve_json_body_arg

        if "default" not in kwargs:
            if "required" not in kwargs:
                # no default? then it's required
                kwargs["required"] = True
            elif not kwargs["required"]:
                raise ValueError(
                    f"Argument '{name}' marked as not required but no default was provided."
                )

        self._argparser.add_argument(f"--{name}", *args, **kwargs)

    @staticmethod
    def _translate_error(
        exc: Union[Exception, SystemExit],
        captured_stderr: str,
    ) -> str:
        """Translate argparse-style error to a message str for HTTPError."""

        # errors not covered by 'exit_on_error=False' (in __init__)
        if isinstance(exc, SystemExit):
            # MISSING ARG
            # ex:
            #   b'foo=val'
            #   {'foo': [b'val']}
            #   ['--foo', 'val']
            # stderr:
            #   usage: __main__.py [---h] --reqd REQD --foo FOO --bar BAR
            #   __main__.py: error: the following arguments are required: --reqd, --bar
            if match := ARGUMENTS_REQUIRED_PATTERN.search(captured_stderr):
                return match.group(1).replace(" --", " ")

            # EXTRA ARG
            # ex:
            #   b'foo=val&reqd=2&xtra=1&another=True&another=False&another=who+knows'
            #   {'foo': [b'val'], 'reqd': [b'2'], 'xtra': [b'1'], 'another': [b'True', b'False', b'who knows']}
            #   ['--foo', 'val', '--reqd', '2', '--xtra', '1', '--another', 'True', 'False', 'who knows']
            # stderr:
            #   usage: __main__.py [---h] --reqd REQD --foo FOO
            #   __main__.py: error: unrecognized arguments: --xtra 1 --another True False who knows
            elif match := UNRECOGNIZED_ARGUMENTS_PATTERN.search(captured_stderr):
                args = (
                    k.replace("--", "")
                    for k in match.group(2).split()
                    if k.startswith("--")
                )
                return f"{match.group(1)} {', '.join(args)}"

        # INVALID VALUE -- not a system error bc 'exit_on_error=False' (in __init__)
        # ex:
        #   argument --foo: invalid int value: 'hank'
        elif isinstance(exc, argparse.ArgumentError):
            if match := INVALID_VALUE_PATTERN.search(str(exc)):
                return f"{match.group(1).replace('--', '')} type"

        # FALL-THROUGH -- log unknown exception
        ts = time.time()  # log timestamp to aid debugging
        LOGGER.error(type(exc))
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        LOGGER.exception(exc)
        LOGGER.error(f"error timestamp: {ts}")
        LOGGER.error(captured_stderr)
        return f"Unknown argument-handling error ({ts})"

    def parse_args(self) -> argparse.Namespace:
        """Get the args -- like argparse.parse_args but parses a dict."""
        arg_strings: List[str] = []

        # json-encoded body arguments
        if self.argument_source == ArgumentSource.JSON_BODY_ARGUMENTS:
            for key, _ in self.rest_handler.json_body_arguments.items():
                arg_strings.append(f"--{key}")
                # use cached value (see add_argument()) to avoid unneeded encoding & decoding
                arg_strings.append(USE_CACHED_VALUE_PLACEHOLDER)
        # query arguments
        elif self.argument_source == ArgumentSource.QUERY_ARGUMENTS:
            for key, vlist in self.rest_handler.request.arguments.items():
                arg_strings.append(f"--{key}")
                arg_strings.extend(to_unicode(v) for v in vlist)
        # error
        else:
            raise ValueError(f"Invalid argument_source: {self}")

        # parse
        with contextlib.redirect_stderr(io.StringIO()) as f:
            try:
                return self._argparser.parse_args(args=arg_strings)
            except (Exception, SystemExit) as e:
                exc = e
                captured_stderr = f.getvalue()
        # handle exception outside of context manager
        msg = self._translate_error(exc, captured_stderr)
        raise tornado.web.HTTPError(400, reason=msg)
