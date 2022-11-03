"""Handle argument parsing, defaulting, and casting."""


import json
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

import tornado.web
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


class ArgumentHandler:
    """Helper class for argument parsing, defaulting, and casting.

    Like argparse.ArgumentParser, but for REST & JSON-body arguments.
    """

    @staticmethod
    def _cast_type(
        value: Any,
        type_: Type[T],
        server_side_error: bool = False,
    ) -> T:
        """Cast `value` to `cast_type` type.

        Keyword Arguments:
            server_side_error {bool} -- *see "Raises" below* (default: {False})

        Raises:
            ValueError -- if typecast fails and `server_side_error=True`
            _InvalidArgumentError -- if typecast fails and `server_side_error=False`
        """
        if type_ is None:
            raise ValueError("argument 'type_' cannot be 'None'")

        try:
            if value is None:
                raise ValueError(
                    f"value cannot be cast to {type_.__name__} from 'None'"
                )
            elif isinstance(value, str) and (type_ == bool) and (value != ""):
                value = strtobool(value)  # ~> ValueError
            else:
                value = type_(value)  # type: ignore  # ~> ValueError or TypeError
        except (ValueError, TypeError) as e:
            if server_side_error:
                raise
            else:
                raise _InvalidArgumentError(f"(ValueError) {e}")

        return value

    @staticmethod
    def _validate_choice(
        value: T, choices: Optional[List[Any]], forbiddens: Optional[List[Any]]
    ) -> T:
        """Check that `value` is in `choices` and not in `forbiddens`.

        Raise _InvalidArgumentError if qualification fails.
        """
        if choices is not None and value not in choices:
            # choices=[] is weird, but is still valid
            raise _InvalidArgumentError(
                f"(ValueError) {value} not in choices ({choices})"
            )

        if forbiddens and value in forbiddens:
            # [] === None: (an empty forbiddens list is the same as no forbiddens list)
            raise _InvalidArgumentError(
                f"(ValueError) {value} is forbidden ({forbiddens})"
            )

        return value

    @staticmethod
    def get_json_body_argument(  # pylint: disable=R0913
        request_body: bytes,
        name: str,
        default: Any,
        type_: Optional[Type[T]],
        choices: Optional[List[Any]],
        forbiddens: Optional[List[Any]],
    ) -> T:
        """Get argument from the JSON-decoded request-body."""
        try:  # first, assume arg is required
            value = _parse_json_body_arguments(request_body)[name]
            if type_:
                value = ArgumentHandler._cast_type(value, type_)
            return ArgumentHandler._validate_choice(value, choices, forbiddens)
        except (KeyError, json.decoder.JSONDecodeError):
            # Required -> raise 400
            if isinstance(default, type(NO_DEFAULT)):
                raise _make_400_error(name, tornado.web.MissingArgumentError(name))
        except _InvalidArgumentError as e:
            raise _make_400_error(name, e)

        # Else: Optional (aka use default value)
        try:
            return ArgumentHandler._validate_choice(default, choices, forbiddens)
        except _InvalidArgumentError as e:
            raise _make_400_error(name, e)

    @staticmethod
    def get_argument(  # pylint: disable=W0221,R0913
        request_body: bytes,
        rest_handler_get_argument: Callable[..., Optional[str]],
        name: str,
        default: Any,
        strip: bool,
        type_: Optional[Type[T]],
        choices: Optional[List[Any]],
        forbiddens: Optional[List[Any]],
    ) -> T:
        """Get argument from query base-arguments / JSON-decoded request-body.

        Try from `get_json_body_argument()` first, then from
        `request_handler.get_argument()`.
        """
        # If: Required -> raise 400
        if isinstance(default, type(NO_DEFAULT)):
            # check JSON-body arguments
            try:
                return ArgumentHandler.get_json_body_argument(
                    request_body, name, NO_DEFAULT, type_, choices, forbiddens
                )
            except tornado.web.MissingArgumentError:
                pass
            except _InvalidArgumentError as e:
                raise _make_400_error(name, e)
            # check query/base and body arguments
            try:
                str_val = rest_handler_get_argument(name, strip=strip)
                if type_:
                    return ArgumentHandler._validate_choice(
                        ArgumentHandler._cast_type(str_val, type_),
                        choices,
                        forbiddens,
                    )
                else:
                    return cast(
                        # this was Optional[str] but that info would get lost anyways
                        Any,
                        ArgumentHandler._validate_choice(str_val, choices, forbiddens),
                    )
            except (tornado.web.MissingArgumentError, _InvalidArgumentError) as e:
                raise _make_400_error(name, e)

        # Else: Optional (aka use default value)
        if default is not None and type_:
            ArgumentHandler._cast_type(default, type_, server_side_error=True)
        # check JSON-body arguments
        try:  # DON'T pass `default` b/c we want to know if there ISN'T a value
            return ArgumentHandler.get_json_body_argument(
                request_body, name, NO_DEFAULT, type_, choices, forbiddens
            )
        except tornado.web.MissingArgumentError:
            pass  # OK. Next, we'll try query base-arguments...
        except _InvalidArgumentError as e:
            raise _make_400_error(name, e)
        # check query base-arguments
        try:
            str_val = rest_handler_get_argument(name, default, strip=strip)
            if type_:
                return ArgumentHandler._validate_choice(
                    ArgumentHandler._cast_type(str_val, type_),
                    choices,
                    forbiddens,
                )
            else:
                return cast(
                    # this was Optional[str] but that info would get lost anyways
                    Any,
                    ArgumentHandler._validate_choice(str_val, choices, forbiddens),
                )
        except _InvalidArgumentError as e:
            raise _make_400_error(name, e)
