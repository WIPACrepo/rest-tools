"""Test server/arghandler.py."""

# pylint: disable=W0212,W0621

import json
import urllib
from typing import Any
from unittest.mock import Mock, patch

import pytest  # type: ignore[import]
import requests
import tornado.web
from rest_tools.server.arghandler import ArgumentHandler, ArgumentSource
from rest_tools.server.handler import RestHandler
from tornado import httputil
from wipac_dev_tools import strtobool

# def test_00_cast_type() -> None:
#     """Test `_cast_type()`."""
#     # None - no casting
#     # assert ArgumentHandler._cast_type("string", None) == "string"
#     # assert ArgumentHandler._cast_type("0", None) == "0"
#     # assert ArgumentHandler._cast_type("2.5", None) == "2.5"
#     # str
#     assert ArgumentHandler._cast_type("string", str) == "string"
#     assert ArgumentHandler._cast_type("", str) == ""
#     assert ArgumentHandler._cast_type(0, str) == "0"
#     # int
#     assert ArgumentHandler._cast_type("1", int) == 1
#     assert ArgumentHandler._cast_type(1.0, int) == 1
#     assert ArgumentHandler._cast_type("1", int) != "1"
#     # float
#     assert ArgumentHandler._cast_type("2.5", float) == 2.5
#     assert ArgumentHandler._cast_type("2.0", float) == 2.0
#     assert ArgumentHandler._cast_type("123", float) == 123.0
#     assert ArgumentHandler._cast_type(4, float) == 4.0
#     # True
#     assert ArgumentHandler._cast_type("1", bool) is True
#     assert ArgumentHandler._cast_type(1, bool) is True
#     assert ArgumentHandler._cast_type(-99, bool) is True
#     for trues in ["True", "T", "On", "Yes", "Y"]:
#         for val in [
#             trues.upper(),
#             trues.lower(),
#             trues[:-1] + trues[-1].upper(),  # upper only last char
#         ]:
#             assert ArgumentHandler._cast_type(val, bool) is True
#     # False
#     assert ArgumentHandler._cast_type("", bool) is False
#     assert ArgumentHandler._cast_type("0", bool) is False
#     assert ArgumentHandler._cast_type(0, bool) is False
#     for falses in ["False", "F", "Off", "No", "N"]:
#         for val in [
#             falses.upper(),
#             falses.lower(),
#             falses[:-1] + falses[-1].upper(),  # upper only last char
#         ]:
#             assert ArgumentHandler._cast_type(val, bool) is False
#     # list
#     assert ArgumentHandler._cast_type("abcd", list) == ["a", "b", "c", "d"]
#     assert ArgumentHandler._cast_type("", list) == []

#     # callable
#     assert ArgumentHandler._cast_type("abcd", len) == 4
#     assert ArgumentHandler._cast_type("abcd", lambda x: 2 * len(x)) == 8

#     def triple_len(val: Any) -> int:
#         return 3 * len(val)

#     assert ArgumentHandler._cast_type("abcd", triple_len) == 12


# def test_01_cast_typ_errors() -> None:
#     """Test `_cast_type()`."""
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._cast_type("", int)
#     assert "(ValueError)" in str(e.value)
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._cast_type("", float)
#     assert "(ValueError)" in str(e.value)
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._cast_type("123abc", float)
#     assert "(ValueError)" in str(e.value)
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._cast_type("anything", bool)
#     assert "(ValueError)" in str(e.value)


# def test_02_validate_choice() -> None:
#     """Test `_validate_choice()`."""
#     ArgumentHandler._validate_choice("foo", None, [])
#     ArgumentHandler._validate_choice("foo", None, None)

#     # choices
#     assert ArgumentHandler._validate_choice(True, [True, False], None) is True
#     assert ArgumentHandler._validate_choice(1, [0, 1, 2], None) == 1
#     assert ArgumentHandler._validate_choice("", [""], None) == ""
#     ArgumentHandler._validate_choice("23", [23, "23"], None)
#     ArgumentHandler._validate_choice("23", [23, r"\d\d"], None)  # regex

#     # forbiddens
#     ArgumentHandler._validate_choice("23", [23, "23"], [])
#     ArgumentHandler._validate_choice("23", [23, "23"], ["boo!"])
#     ArgumentHandler._validate_choice("23", ["23"], [23])
#     ArgumentHandler._validate_choice(["list"], None, [list(), dict()])


# def test_03_validate_choice__errors() -> None:
#     """Test `_validate_choice()`."""
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("23", [23], None)
#     assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("string", ["STRING"], None)
#     assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("3", [0, 1, 2], None)
#     assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("abc", [["a", "b", "c", "d"]], None)
#     assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("foo", [], [])  # no allowed choices
#     assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)

#     # forbiddens
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("23", None, ["23"])
#     assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("baz", ["baz"], ["baz"])
#     assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice([], None, [list(), dict()])
#     assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice({}, None, [list(), dict()])
#     assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)
#     #
#     with pytest.raises(_InvalidArgumentError) as e:
#         ArgumentHandler._validate_choice("   ", None, [123, r"\s*"])  # regex
#     assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)


# def test_04_cast_type() -> None:
#     """Test `_cast_type()`."""
#     vals = [
#         "abcdefghijklmopqrstuvwxyz",
#         1,
#         None,
#         ["this is", "a list"],
#         "",
#         2.5,
#         {"but this": "is a dict"},
#     ]

#     def _agreeable_type(typ: Any, val: Any) -> bool:
#         if val is None:
#             return False
#         try:
#             typ(val)
#             return True
#         except Exception:
#             return False

#     for val in vals:
#         print(val)
#         # Passing Cases:
#         # assert val == ArgumentHandler._cast_type(val, None)  # None is always allowed
#         for o_type in [type(o) for o in vals if _agreeable_type(type(o), val)]:
#             print(o_type)
#             out = ArgumentHandler._cast_type(val, o_type)
#             assert isinstance(out, o_type)

#         # Error Cases:

#         # None is not allowed (unless the type is type(None))
#         if val is not None:
#             with pytest.raises(_InvalidArgumentError):
#                 ArgumentHandler._cast_type(None, type(val))
#             with pytest.raises((ValueError, TypeError)):
#                 ArgumentHandler._cast_type(None, type(val), server_side_error=True)

#         # type-mismatch  # pylint: disable=C0123
#         for o_type in [type(o) for o in vals if not _agreeable_type(type(o), val)]:
#             print(o_type)
#             with pytest.raises(_InvalidArgumentError):
#                 ArgumentHandler._cast_type(val, o_type)
#             with pytest.raises((ValueError, TypeError)):
#                 ArgumentHandler._cast_type(val, o_type, server_side_error=True)


# def test_05_strict_type() -> None:
#     """Test `_cast_type(strict_type=True)`."""
#     bad_vals = {
#         str: [1, [], False],
#         bool: [1, "True", [], [False]],
#         int: [2.1, 9.0, "10", [], [5]],
#         list: ["not a list", {"a": 1}, 1],
#         float: [2, "1e4", [], [1.0]],
#     }

#     for o_type, values in bad_vals.items():
#         for val in values:
#             with pytest.raises(_InvalidArgumentError):
#                 ArgumentHandler._cast_type(val, o_type, strict_type=True)
#             with pytest.raises((ValueError, TypeError)):
#                 ArgumentHandler._cast_type(
#                     val, o_type, strict_type=True, server_side_error=True
#                 )

QUERY_ARGUMENTS = "query-arguments"
JSON_BODY_ARGUMENTS = "json-body-arguments"


def setup_argument_handler(
    argument_source: str,
    args: dict[str, Any] | list[tuple[Any, Any]],
) -> httputil.HTTPServerRequest:
    if argument_source == QUERY_ARGUMENTS:
        req = requests.Request(url="https://foo.aq/all", params=args).prepare()
        print("\n request:")
        print(req.url)
        print()
        rest_handler = RestHandler(
            application=Mock(),
            request=httputil.HTTPServerRequest(
                uri=req.url,
                headers=req.headers,
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
                body=req.body,
                headers=req.headers,
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

    for default in [None, "string", 100, 50.5]:
        print(default)
        arghand = setup_argument_handler(argument_source, {})
        arghand.add_argument("myarg", default=default)
        args = arghand.parse_args()
        assert default == args.myarg

    # w/ typing
    for default in ["string", 100, 50.5]:
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
    args = {
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
        assert val == getattr(outargs, arg)


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_111__no_default_with_typing(argument_source: str) -> None:
    """Test `request.arguments` arguments."""
    args = {
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
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        pass

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
        if typ == bool:
            assert getattr(outargs, arg) == strtobool(val)
        else:
            assert getattr(outargs, arg) == typ(val)

    # NOTE - `default` non-error use-cases solely on RequestHandler.get_argument(), so no tests
    # NOTE - `strip` use-cases depend solely on RequestHandler.get_argument(), so no tests
    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, JSON_BODY_ARGUMENTS],
)
def test_112__no_default_with_typing__error(argument_source: str) -> None:
    """Test `argument_source` arguments."""
    args = {
        "foo": ("hank", int),
        "bat": ("2.5", int),
        "baz": ("9e-33", int),
        #
        "bar": ("idk", bool),
        "boo": ("2", bool),
        #
        "abc": ("222.111.333", float),
    }
    if argument_source == JSON_BODY_ARGUMENTS:
        pass

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

    # NOTE - `typ` and `choices` are tested in `_qualify_argument` tests


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

    # NOTE - `typ` and `choices` are tested in `_qualify_argument` tests


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
        pass

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, args)
    arghand.add_argument("foo", type=int, nargs="*")
    arghand.add_argument("baz", type=str, nargs="*")
    arghand.add_argument("bar")
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
    arghand = setup_argument_handler(
        argument_source,
        [
            ("foo", "val"),
            ("reqd", "2"),
            ("xtra", 1),
            ("another", True),
            ("another", False),
            ("another", "who knows"),
        ],
    )
    if argument_source == JSON_BODY_ARGUMENTS:
        pass
    arghand.add_argument("reqd")
    arghand.add_argument("foo")

    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()
    assert str(e.value) == "HTTP 400: unrecognized arguments: xtra, another"
