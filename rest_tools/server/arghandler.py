"""Handle argument parsing, defaulting, and casting."""


import distutils.util
import json
from typing import Any, cast, Dict, List, Optional

import tornado.web

from ..utils.json_util import json_decode


class _NoDefaultValue:  # pylint: disable=R0903
    """Signal no default value, AKA argument is required."""


NO_DEFAULT = _NoDefaultValue()


def _get_json_body_arguments(
    request_handler: tornado.web.RequestHandler,
) -> Dict[str, Any]:
    """Return the request body JSON-decoded, but only if it's a `dict`."""
    json_body = json_decode(request_handler.request.body)  # type: ignore[no-untyped-call]

    if isinstance(json_body, dict):
        return cast(Dict[str, Any], json_body)
    return {}


class _UnqualifiedArgumentError(Exception):
    """Raise when ArgumentHandler._qualify_argument() fails."""


def _make_400_error(arg_name: str, error: Exception) -> tornado.web.HTTPError:
    if isinstance(error, tornado.web.MissingArgumentError):
        return error  # MissingArgumentError is already a 400 error
    return tornado.web.HTTPError(400, reason=f"`{arg_name}`: {error}")


class ArgumentHandler:
    """Helper class for argument parsing, defaulting, and casting.

    Like argparse.ArgumentParser, but for REST & JSON-body arguments.
    """

    @staticmethod
    def _qualify_argument(
        type_: Optional[type], choices: Optional[List[Any]], value: Any
    ) -> Any:
        """Cast `value` to `type_` type, and/or check `value` in in `choices`.

        Raise _UnqualifiedArgumentError if either qualification fails.
        """
        if type_:
            try:
                if isinstance(value, str) and (type_ == bool) and (value != ""):
                    value = bool(distutils.util.strtobool(value))
                else:
                    value = type_(value)
            except ValueError as e:
                raise _UnqualifiedArgumentError(f"(ValueError) {e}")

        if choices and (value not in choices):
            raise _UnqualifiedArgumentError(
                f"(ValueError) {value} not in options ({choices})"
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
        choices: Optional[List[Any]],
    ) -> Any:
        """Return the argument from JSON-decoded request body."""
        try:
            value = _get_json_body_arguments(request_handler)[name]
            return ArgumentHandler._qualify_argument(None, choices, value)
        except (KeyError, json.decoder.JSONDecodeError):
            # Required -> raise 400
            if isinstance(default, type(NO_DEFAULT)):
                raise _make_400_error(name, tornado.web.MissingArgumentError(name))
        except _UnqualifiedArgumentError as e:
            raise _make_400_error(name, e)

        # Else:
        # Optional / Default
        try:
            return ArgumentHandler._qualify_argument(None, choices, default)
        except _UnqualifiedArgumentError as e:
            raise _make_400_error(name, e)

    @staticmethod
    def get_argument(  # pylint: disable=W0221,R0913
        request_handler: tornado.web.RequestHandler,
        name: str,
        default: Any,
        strip: bool,
        type_: Optional[type],
        choices: Optional[List[Any]],
    ) -> Any:
        """Return argument from query arguments or JSON request body.

        Try from `get_json_body_argument()` first, then from
        `request_handler.get_argument()`.
        """
        # If:
        # Required -> raise 400
        if isinstance(default, type(NO_DEFAULT)):
            # check JSON-body arguments
            try:
                json_arg = ArgumentHandler.get_json_body_argument(
                    request_handler, name, NO_DEFAULT, choices
                )
                return ArgumentHandler._qualify_argument(type_, choices, json_arg)
            except tornado.web.MissingArgumentError:
                pass
            except _UnqualifiedArgumentError as e:
                raise _make_400_error(name, e)
            # check query and body arguments
            try:
                arg = request_handler.get_argument(name, strip=strip)
                return ArgumentHandler._qualify_argument(type_, choices, arg)
            except (tornado.web.MissingArgumentError, _UnqualifiedArgumentError) as e:
                raise _make_400_error(name, e)

        # Else:
        # Optional / Default
        ArgumentHandler._type_check(type_, default)
        # check JSON-body arguments
        try:  # DON'T pass `default` b/c we want to know if there ISN'T a value
            json_arg = ArgumentHandler.get_json_body_argument(
                request_handler, name, NO_DEFAULT, choices
            )
            return ArgumentHandler._qualify_argument(type_, choices, json_arg)
        except tornado.web.MissingArgumentError:
            pass  # OK. Next, we'll try query arguments...
        except _UnqualifiedArgumentError as e:
            raise _make_400_error(name, e)
        # check query and body arguments
        arg = request_handler.get_argument(name, default, strip=strip)
        try:
            return ArgumentHandler._qualify_argument(type_, choices, arg)
        except _UnqualifiedArgumentError as e:
            raise _make_400_error(name, e)
