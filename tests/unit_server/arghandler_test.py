"""Test server/arghandler.py."""

import argparse
import json
import re
import sys
from typing import Any, Union, cast
from unittest.mock import Mock

import pytest
import requests
import tornado.web
from tornado import httputil
from wipac_dev_tools import strtobool

from rest_tools.server.arghandler import ArgumentHandler, ArgumentSource
from rest_tools.server.handler import RestHandler

# pylint: disable=W0212,W0621

# these tests are only for 3.9+
if sys.version_info < (3, 9):
    pytest.skip("only for 3.9+", allow_module_level=True)  # type: ignore[var-annotated]

QUERY_ARGUMENTS = "query-arguments"
JSON_BODY_ARGUMENTS = "json-body-arguments"


def setup_argument_handler(
    argument_source: str,
    args: Union[dict[str, Any], list[tuple[Any, Any]]],
) -> ArgumentHandler:
    """Load data and return `ArgumentHandler` instance."""
    if argument_source == QUERY_ARGUMENTS:
        req = requests.Request(url="https://foo.aq/all", params=args).prepare()
        print("\n request:")
        print(req.url)
        print()
        rest_handler = RestHandler(
            application=Mock(),
            request=httputil.HTTPServerRequest(
                uri=req.url,
                headers=httputil.HTTPHeaders(req.headers),
            ),
        )
        return ArgumentHandler(ArgumentSource.QUERY_ARGUMENTS, rest_handler)

    elif argument_source == JSON_BODY_ARGUMENTS:
        req = requests.Request(url="https://foo.aq/all", json=args).prepare()
        print("\n request:")
        print(req.url)
        print(req.body)
        print(req.headers)
        print()
        rest_handler = RestHandler(
            application=Mock(),
            request=httputil.HTTPServerRequest(
                uri=req.url,
                body=cast(bytes, req.body),
                headers=httputil.HTTPHeaders(req.headers),
            ),
        )
        rest_handler.request._parse_body()  # normally called when request REST method starts
        print("\n rest-handler:")
        print(rest_handler.request.body)
        print(json.loads(rest_handler.request.body))
        print()
        return ArgumentHandler(ArgumentSource.JSON_BODY_ARGUMENTS, rest_handler)

    else:
        raise ValueError(f"Invalid argument_source: {argument_source}")


########################################################################################


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_100__defaults(argument_source: str) -> None:
    """Test `argument_source` arguments with default."""
    default: Any

    for default in [None, "a-string", 100, 50.5]:
        print(default)
        arghand = setup_argument_handler(argument_source, {})
        arghand.add_argument("myarg", default=default)
        args = arghand.parse_args()
        assert default == args.myarg

    # w/ typing
    for default in ["a-string", 100, 50.5]:
        print(default)
        arghand = setup_argument_handler(argument_source, {})
        arghand.add_argument("myarg", default=default, type=type(default))
        args = arghand.parse_args()
        assert default == args.myarg


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_110__no_default_no_typing(argument_source: str) -> None:
    """Test `argument_source` arguments."""
    args: dict[str, Any] = {
        "foo": "-10",
        "bar": "True",
        "bat": "2.5",
        "baz": "Toyota Corolla",
        "boo": "False",
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args.update(
            {
                "dicto": {"abc": 123},
                "listo": [1, 2, 3],
                "falso": False,
                "truo": True,
                "compoundo": [{"apple": True}, {"banana": 951}, {"cucumber": False}],
            }
        )

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, args)

    for arg, _ in args.items():
        print()
        print(arg)
        arghand.add_argument(arg)
    outargs = arghand.parse_args()

    # grab each
    for arg, val in args.items():
        print()
        print(arg)
        print(val)
        assert val == getattr(outargs, arg.replace("-", "_"))


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_111__no_default_with_typing(argument_source: str) -> None:
    """Test `request.arguments` arguments."""

    def custom_type(_: Any) -> Any:
        return "this could be anything but it's just a string"

    args: dict[str, Any] = {
        "foo": ("-10", int),
        #
        "bar": ("True", bool),
        "boo": ("False", bool),
        "ghi": ("no", bool),
        "jkl": ("1", bool),
        "mno": ("0", bool),
        #
        "bat": ("2.5", float),
        "abc": ("2", float),
        #
        "baz": ("Toyota Corolla", str),
        "def": ("1000", str),
        #
        "zzz": ("yup", custom_type),
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args.update(
            {
                "dicto": ({"abc": 123}, dict),
                "dicto-as-list": ({"def": 456}, list),
                "listo": ([1, 2, 3], list),
                "falso": (False, bool),
                "truo": (True, bool),
                "compoundo": (
                    [{"apple": True}, {"banana": 951}, {"cucumber": False}],
                    list,
                ),
                "sure": (
                    [{"apple": True}, {"banana": 951}, {"cucumber": False}],
                    custom_type,
                ),
            }
        )

    # set up ArgumentHandler
    arghand = setup_argument_handler(
        argument_source, {arg: val for arg, (val, _) in args.items()}
    )
    for arg, (_, typ) in args.items():
        print()
        print(arg)
        arghand.add_argument(arg, type=typ)
    outargs = arghand.parse_args()

    # grab each
    for arg, (val, typ) in args.items():
        print()
        print(arg)
        print(val)
        print(typ)
        if typ == bool and isinstance(val, str):
            assert getattr(outargs, arg.replace("-", "_")) == strtobool(val)
        else:
            assert getattr(outargs, arg.replace("-", "_")) == typ(val)


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_112__no_default_with_typing__error(argument_source: str) -> None:
    """Test `argument_source` arguments."""

    def custom_type(val: Any) -> Any:
        raise ValueError("x")

    args: dict[str, Any] = {
        "foo": ("hank", int),
        "bat": ("2.5", int),
        "baz": ("9e-33", int),
        #
        "bar": ("idk", bool),
        "boo": ("2", bool),
        #
        "abc": ("222.111.333", float),
        #
        "zzz": ("yup", custom_type),
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args.update(
            {
                "dicto": ({"abc": 123}, int),
                "listo": ([1, 2, 3], int),
                "compoundo": (
                    [{"apple": True}, {"banana": 951}, {"cucumber": False}],
                    object,
                ),
                "nope": (
                    [{"apple": True}, {"banana": 951}, {"cucumber": False}],
                    custom_type,
                ),
            }
        )

    for arg, (val, typ) in args.items():
        print()
        print(arg)
        print(val)
        print(typ)
        arghand = setup_argument_handler(argument_source, {arg: val})
        arghand.add_argument(arg, type=typ)
        with pytest.raises(tornado.web.HTTPError) as e:
            arghand.parse_args()
        assert str(e.value) == f"HTTP 400: argument {arg}: invalid type"


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_120__missing_argument(argument_source: str) -> None:
    """Test `argument_source` arguments error case."""

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, {})
    arghand.add_argument("reqd")

    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()
    assert str(e.value) == "HTTP 400: the following arguments are required: reqd"


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_121__missing_argument(argument_source: str) -> None:
    """Test `argument_source` arguments error case."""

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, {"foo": "val"})
    arghand.add_argument("reqd")
    arghand.add_argument("foo")
    arghand.add_argument("bar")

    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()
    assert str(e.value) == "HTTP 400: the following arguments are required: reqd, bar"


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_130__duplicates(argument_source: str) -> None:
    """Test `argument_source` arguments with duplicate keys."""

    args = [
        ("foo", "22"),
        ("foo", "44"),
        ("foo", "66"),
        ("foo", "88"),
        ("bar", "abc"),
        ("baz", "hello world!"),
        ("baz", "hello mars!"),
    ]
    if argument_source == JSON_BODY_ARGUMENTS:
        pass  # no special data since duplicates not allowed for json

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, args)
    arghand.add_argument("foo", type=int, nargs="*")
    arghand.add_argument("baz", type=str, nargs="*")
    arghand.add_argument("bar")

    # duplicates not allowed for json
    if argument_source == JSON_BODY_ARGUMENTS:
        with pytest.raises(tornado.web.HTTPError) as e:
            arghand.parse_args()
        assert str(e.value) == "HTTP 400: JSON-encoded requests body must be a 'dict'"
    # but they are for query args!
    else:
        outargs = arghand.parse_args()
        print(outargs)
        # grab each
        assert outargs.foo == [22, 44, 66, 88]
        assert outargs.baz == ["hello world!", "hello mars!"]
        assert outargs.bar == "abc"


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_140__extra_argument(argument_source: str) -> None:
    """Test `argument_source` arguments error case."""

    # set up ArgumentHandler
    args: dict[str, Any] = {
        "foo": "val",
        "reqd": "2",
        "xtra": 1,
        "another": True,
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args["another"] = [{"apple": True}, {"banana": 951}, {"cucumber": False}]

    arghand = setup_argument_handler(argument_source, args)
    arghand.add_argument("reqd")
    arghand.add_argument("foo")

    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()
    assert str(e.value) == "HTTP 400: unrecognized arguments: xtra, another"


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_141__extra_argument_with_duplicates(argument_source: str) -> None:
    """Test `argument_source` arguments error case."""

    # set up ArgumentHandler
    args = [
        ("foo", "val"),
        ("reqd", "2"),
        ("xtra", 1),
        ("another", True),
        ("another", False),
        ("another", "who knows"),
    ]
    if argument_source == JSON_BODY_ARGUMENTS:
        pass  # no special data since duplicates not allowed for json

    arghand = setup_argument_handler(argument_source, args)
    arghand.add_argument("reqd")
    arghand.add_argument("foo")

    # Missing Required Argument...

    # duplicates not allowed for json
    if argument_source == JSON_BODY_ARGUMENTS:
        with pytest.raises(tornado.web.HTTPError) as e:
            arghand.parse_args()
        assert str(e.value) == "HTTP 400: JSON-encoded requests body must be a 'dict'"
    # but they are for query args!
    else:
        with pytest.raises(tornado.web.HTTPError) as e:
            arghand.parse_args()
        assert str(e.value) == "HTTP 400: unrecognized arguments: xtra, another"


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_200__argparse_dest(argument_source: str) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    args: dict[str, Any] = {
        "old_name": "-10",
        "bar": "True",
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args.update(
            {
                "dicto": {"abc": 123},
                "listo": [1, 2, 3],
            }
        )

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, args)

    for arg, _ in args.items():
        print()
        print(arg)
        if arg == "old_name":
            arghand.add_argument(arg, dest="new_name")
        else:
            arghand.add_argument(arg)
    outargs = arghand.parse_args()

    # grab each
    for arg, val in args.items():
        print()
        print(arg)
        print(val)
        if arg == "old_name":
            assert val == getattr(outargs, "new_name")
        else:
            assert val == getattr(outargs, arg.replace("-", "_"))


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_210__argparse_choices(argument_source: str) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    args: dict[str, Any] = {
        "pick_it": "paper",
        "bar": "True",
    }
    choices: list = ["rock", "paper", "scissors"]
    if argument_source == JSON_BODY_ARGUMENTS:
        args.update(
            {
                "pick_it": {"abc": 123},
                "listo": [1, 2, 3],
            }
        )
        choices = [{"abc": 123}, {"def": 456}, {"ghi": 789}]

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, args)

    for arg, _ in args.items():
        print()
        print(arg)
        if arg == "pick_it":
            arghand.add_argument(arg, choices=choices)
        else:
            arghand.add_argument(arg)
    outargs = arghand.parse_args()

    # grab each
    for arg, val in args.items():
        print()
        print(arg)
        print(val)
        assert val == getattr(outargs, arg.replace("-", "_"))


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_211__argparse_choices__error(argument_source: str) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    args: dict[str, Any] = {
        "pick_it": "paper",
        "bar": "True",
    }
    choices: list[Any] = ["rock", "paper", "scissors"]
    if argument_source == JSON_BODY_ARGUMENTS:
        args.update(
            {
                "pick_it": {"abc": 123},
                "listo": [1, 2, 3],
            }
        )
        choices = [{"abc": 123}, {"def": 456}, {"ghi": 789}]

    # set up ArgumentHandler
    arghand = setup_argument_handler(
        argument_source,
        {k: v if k != "pick_it" else "hank" for k, v in args.items()},
    )

    for arg, _ in args.items():
        print()
        print(arg)
        if arg == "pick_it":
            arghand.add_argument(arg, choices=choices)
        else:
            arghand.add_argument(arg)

    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()

    # For Python 3.13 and later: join stringified representations directly
    expected_message1 = (
        f"HTTP 400: argument pick_it: invalid choice: 'hank' "
        f"(choose from {', '.join(str(c) for c in choices)})"
    )
    # For Python 3.9–3.12: join repr representations directly
    expected_message2 = (
        f"HTTP 400: argument pick_it: invalid choice: 'hank' "
        f"(choose from {', '.join(repr(c) for c in choices)})"
    )
    assert (
        str(e.value) == expected_message1 or str(e.value) == expected_message2
    ), "Error does not match expected values"


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_220__argparse_nargs(argument_source: str) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    test_130__duplicates(argument_source)


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
@pytest.mark.parametrize(
    "exc",
    [TypeError, ValueError, argparse.ArgumentError],
)
def test_230__argparse_custom_validation__supported_builtins__error(
    argument_source: str, exc: Exception
) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    args: dict[str, Any] = {
        "foo": "True",
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args = {
            "foo": [1, 2, 3],
        }

    # set up ArgumentHandler
    arghand = setup_argument_handler(
        argument_source,
        args,
    )

    def _error_it(_: Any, exc: Exception):
        raise exc

    for arg, _ in args.items():
        print()
        print(arg)
        arghand.add_argument(
            arg,
            type=lambda x: _error_it(
                x,
                exc("it's a bad value but you won't see this message anyway..."),  # type: ignore
            ),
        )

    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()

    assert str(e.value) == "HTTP 400: argument foo: invalid type"


class MyError(Exception):
    """Used below."""


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
@pytest.mark.parametrize(
    "exc",
    [RuntimeError, IndexError, MyError],
)
def test_232__argparse_custom_validation__unsupported_errors__error(
    argument_source: str, exc: Exception
) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    args: dict[str, Any] = {
        "foo": "True",
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args = {
            "foo": [1, 2, 3],
        }

    # set up ArgumentHandler
    arghand = setup_argument_handler(
        argument_source,
        args,
    )

    def _error_it(_: Any, exc: Exception):
        raise exc

    for arg, _ in args.items():
        print()
        print(arg)
        arghand.add_argument(
            arg,
            type=lambda x: _error_it(
                x,
                exc("something went wrong but not in an unexpected way, not-validation"),  # type: ignore
            ),
        )

    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()

    assert re.fullmatch(
        r"HTTP 400: Unknown argument-handling error \(\d+\.\d+\)", str(e.value)
    )


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_234__argparse_custom_validation__argumenttypeerror__error(
    argument_source: str,
) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    args: dict[str, Any] = {
        "foo": "True",
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args = {
            "foo": [1, 2, 3],
        }

    # set up ArgumentHandler
    arghand = setup_argument_handler(
        argument_source,
        args,
    )

    def _error_it(_: Any):
        raise argparse.ArgumentTypeError("it's a bad value and you *will* see this!")

    for arg, _ in args.items():
        print()
        print(arg)
        arghand.add_argument(
            arg,
            type=_error_it,
        )

    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()

    assert (
        str(e.value)
        == "HTTP 400: argument foo: it's a bad value and you *will* see this!"
    )


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
@pytest.mark.parametrize(
    "exc",
    [  # all the exceptions!
        TypeError,
        ValueError,
        argparse.ArgumentError,
        argparse.ArgumentTypeError,
        RuntimeError,
        IndexError,
        MyError,
    ],
)
def test_236__argparse_custom_validation__validator_no_param__error(
    argument_source: str,
    exc: Exception,
) -> None:
    """Test `argument_source` arguments using argparse's advanced options."""
    args: dict[str, Any] = {
        "foo": "True",
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        args = {
            "foo": [1, 2, 3],
        }

    # set up ArgumentHandler
    arghand = setup_argument_handler(
        argument_source,
        args,
    )

    def _error_it__no_param():
        raise exc("it's a bad value and you *will* see this!")  # type: ignore

    for arg, _ in args.items():
        print()
        print(arg)
        arghand.add_argument(
            arg,
            type=_error_it__no_param,
            # NOTE: ^^^ because this takes no arguments (isn't a func/lambda),
            #       argparse treats it like any other error. why? idk :/
        )

    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()

    assert str(e.value) == "HTTP 400: argument foo: invalid type"
