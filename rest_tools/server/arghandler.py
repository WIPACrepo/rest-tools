"""Handle argument parsing, defaulting, and casting."""


import json
from typing import Any, List, Optional

import tornado.web

# local imports
from rest_tools.client.json_util import json_decode


class _NoDefaultValue:  # pylint: disable=R0903
    """Signal no default value, AKA argument is required."""


NO_DEFAULT = _NoDefaultValue()
_FALSES = ["FALSE", "False", "false", "0", 0, "NO", "No", "no"]


class ArgumentHandler:
    """Helper class for argument parsing, defaulting, and casting.

    Like argparse.ArgumentParser, but for REST & JSON-body arguments.
    """

    @staticmethod
    def _qualify_argument(
        type_: Optional[type], choices: Optional[List[Any]], value: Any
    ) -> Any:
        """Cast `value` to `type_` type, and/or check `value` in in `choices`.

        Raise 400 if either qualification fails.
        """
        if type_:
            try:
                if (type_ == bool) and (value in _FALSES):
                    value = False
                else:
                    value = type_(value)
            except ValueError as e:
                raise tornado.web.HTTPError(400, reason=f"(ValueError) {e}")

        if choices and (value not in choices):
            raise tornado.web.HTTPError(
                400, reason=f"(ValueError) {value} not in options ({choices})"
            )

        return value

    @staticmethod
    def _type_check(type_: Optional[type], value: Any) -> None:
        # check the value's type (None is okay too)
        if not type_:
            return
        if not isinstance(value, type_) and (value is not None):
            raise ValueError(
                f"Value, `{value}` ({type(value)}), is not {type_} or None"
            )

    @staticmethod
    def get_json_body_argument(  # pylint: disable=R0913
        request_handler: tornado.web.RequestHandler,
        name: str,
        default: Any,
        strip: bool,
        type_: Optional[type],
        choices: Optional[List[Any]],
    ) -> Any:
        """Return the argument by JSON-decoding the request body."""
        try:
            value = json_decode(request_handler.request.body)[name]  # type: ignore[no-untyped-call]
            if strip and isinstance(value, tornado.util.unicode_type):
                value = value.strip()
            return ArgumentHandler._qualify_argument(type_, choices, value)
        except (KeyError, json.decoder.JSONDecodeError):
            # Required -> raise 400
            if isinstance(default, type(NO_DEFAULT)):
                raise tornado.web.MissingArgumentError(name)

        # Else:
        # Optional / Default
        ArgumentHandler._type_check(type_, default)
        return ArgumentHandler._qualify_argument(type_, choices, default)

    @staticmethod
    def get_argument(  # pylint: disable=W0221,R0913
        request_handler: tornado.web.RequestHandler,
        name: str,
        default: Any,
        strip: bool,
        type_: Optional[type],
        choices: Optional[List[Any]],
    ) -> Any:
        """Return argument. If no default provided raise 400 if not present.

        Try from `get_json_body_argument()` first, then from
        `request_handler.get_argument()`.
        """
        # If:
        # Required -> raise 400
        if isinstance(default, type(NO_DEFAULT)):
            # check JSON'd body arguments
            try:
                return ArgumentHandler.get_json_body_argument(
                    request_handler, name, default, strip, type_, choices
                )
            except tornado.web.MissingArgumentError:
                pass
            # check query and body arguments
            try:
                arg = request_handler.get_argument(name, strip=strip)
                return ArgumentHandler._qualify_argument(type_, choices, arg)
            except tornado.web.MissingArgumentError as e:
                raise tornado.web.HTTPError(400, reason=e.log_message)

        # Else:
        # Optional / Default
        ArgumentHandler._type_check(type_, default)
        # check JSON'd body arguments  # pylint: disable=C0103
        json_arg = ArgumentHandler.get_json_body_argument(
            request_handler, name, default, strip, type_, choices,
        )
        if json_arg != default:
            return json_arg
        # check query and body arguments
        arg = request_handler.get_argument(name, default, strip=strip)
        return ArgumentHandler._qualify_argument(type_, choices, arg)
