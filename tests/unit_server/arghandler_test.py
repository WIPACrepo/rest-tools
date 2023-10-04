"""Test server/arghandler.py."""

# pylint: disable=W0212,W0621

import json
import urllib
from typing import Any
from unittest.mock import Mock, patch

import pytest  # type: ignore[import]
import tornado.web
from rest_tools.server.arghandler import ArgumentHandler, _InvalidArgumentError
from rest_tools.server.handler import RestHandler
from tornado import httputil

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
BODY_ARGUMENTS = "body-arguments"


def setup_argument_handler(
    argument_source: str,
    args: dict[str, Any],
) -> httputil.HTTPServerRequest:
    if argument_source == QUERY_ARGUMENTS:
        rest_handler = RestHandler(
            application=Mock(),
            request=httputil.HTTPServerRequest(
                uri=f"foo.aq/all?{urllib.parse.urlencode(args)}",
            ),
        )
        return ArgumentHandler(rest_handler.request.arguments)
    elif argument_source == BODY_ARGUMENTS:
        rest_handler = RestHandler(
            application=Mock(),
            request=httputil.HTTPServerRequest(
                uri="foo.aq/all",
                body=urllib.parse.urlencode(args).encode("latin1"),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ),
        )
        rest_handler.request._parse_body()  # normally called when request REST method starts
        print(rest_handler.request.body)
        print(rest_handler.request.body_arguments)
        return ArgumentHandler(rest_handler.request.body_arguments)
    else:
        raise ValueError(f"Invalid argument_source: {argument_source}")


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, BODY_ARGUMENTS],
)
def test_100__defaults(argument_source: str) -> None:
    """Test `request.arguments` arguments with default."""
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
    [QUERY_ARGUMENTS, BODY_ARGUMENTS],
)
def test_110__no_default_no_typing(argument_source: str) -> None:
    """Test `request.arguments` arguments."""
    args = {
        "foo": ("-10", int),
        "bar": ("True", bool),
        "bat": ("2.5", float),
        "baz": ("Toyota Corolla", str),
        "boo": ("False", bool),
    }

    # set up ArgumentHandler
    arghand = setup_argument_handler(
        argument_source, {arg: val for arg, (val, _) in args.items()}
    )

    for arg, _ in args.items():
        print()
        print(arg)
        arghand.add_argument(arg)
    outargs = arghand.parse_args()

    # grab each
    for arg, (val, _) in args.items():
        print()
        print(arg)
        print(val)
        # print(typ)
        assert val == getattr(outargs, arg)


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, BODY_ARGUMENTS],
)
def test_111__no_default_with_typing(argument_source: str) -> None:
    """Test `request.arguments` arguments."""
    args = {
        "foo": ("-10", int),
        "bar": ("True", bool),
        "bat": ("2.5", float),
        "baz": ("Toyota Corolla", str),
        "boo": ("False", bool),
    }

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
            if val == "False":
                assert getattr(outargs, arg) is False
            elif val == "True":
                assert getattr(outargs, arg) is True
            else:
                raise RuntimeError("Invalid value")
        else:
            assert getattr(outargs, arg) == typ(val)

    # NOTE - `default` non-error use-cases solely on RequestHandler.get_argument(), so no tests
    # NOTE - `strip` use-cases depend solely on RequestHandler.get_argument(), so no tests
    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, BODY_ARGUMENTS],
)
def test_120__missing_argument(argument_source: str) -> None:
    """Test `request.arguments` arguments error case."""

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, {})
    arghand.add_argument("reqd")

    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()
    error_msg = "HTTP 400: the following arguments are required: reqd"
    assert str(e.value) == error_msg

    # NOTE - `typ` and `choices` are tested in `_qualify_argument` tests


@pytest.mark.parametrize(
    "argument_source",
    [QUERY_ARGUMENTS, BODY_ARGUMENTS],
)
def test_121__missing_argument(argument_source: str) -> None:
    """Test `request.arguments` arguments error case."""

    # set up ArgumentHandler
    arghand = setup_argument_handler(argument_source, {"foo": "val"})
    arghand.add_argument("reqd")
    arghand.add_argument("foo")

    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        arghand.parse_args()
    error_msg = "HTTP 400: the following arguments are required: reqd"
    assert str(e.value) == error_msg

    # NOTE - `typ` and `choices` are tested in `_qualify_argument` tests


# def test_30_get_json_body_argument() -> None:
#     """Test `request.body` JSON arguments."""
#     body = {"green": 10, "eggs": True, "and": "wait for it...", "ham": [1, 2, 4]}

#     # Simple Use Cases
#     for arg, val in body.items():
#         print(arg)
#         pjba.return_value = body
#         assert val == rest_handler.get_json_body_argument(arg)

#     # Default Use Cases
#     for arg, val in body.items():
#         print(arg)
#         pjba.return_value = {a: v for a, v in body.items() if a != arg}
#         assert "Terry" == rest_handler.get_json_body_argument(arg, default="Terry")

#     # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


# def test_31_get_json_body_argument__errors() -> None:
#     """Test `request.body` JSON arguments."""
#     body = {"green": 10, "eggs": True, "and": "wait for it...", "ham": [1, 2, 4]}

#     # Missing Required Argument
#     with pytest.raises(tornado.web.HTTPError) as e:
#         pjba.return_value = body
#         rest_handler.get_json_body_argument("Reqd")
#     error_msg = "HTTP 400: `Reqd`: (MissingArgumentError) required argument is missing"
#     assert str(e.value) == error_msg

#     # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


# def test_32_get_json_body_argument_typechecking() -> None:
#     """Test `get_json_body_argument()`.

#     **Test JSON-body arg type-checking**
#     """
#     pjba.return_value = {"foo": "99.9"}

#     ret = rest_handler.get_json_body_argument("foo", default=None, type=str)

#     pjba.assert_called()
#     assert ret == "99.9"

#     # # #

#     pjba.return_value = {"foo": ["a", "bc"]}

#     ret2 = rest_handler.get_json_body_argument("foo", default=None, type=list)

#     pjba.assert_called()
#     assert ret2 == ["a", "bc"]


# def test_33_get_json_body_argument_typechecking__errors(
#     ,
# ) -> None:
#     """Test `get_json_body_argument()`.

#     If there's a matching argument in JSON-body, but it's the wrong
#     type, raise 400.
#     """
#     pjba.return_value = {"foo": "NINETY-NINE"}

#     with pytest.raises(tornado.web.HTTPError) as e:
#         rest_handler.get_json_body_argument("foo", default=None, type=float)
#     error_msg = (
#         "HTTP 400: `foo`: (ValueError) could not convert string to float: 'NINETY-NINE'"
#     )
#     assert str(e.value) == error_msg

#     pjba.assert_called()


# def test_40_get_argument_args_and_body() -> None:
#     """Test `get_argument()`.

#     From JSON-body (no Query-Args)
#     """
#     # TODO - patch based on argument: https://stackoverflow.com/a/16162316/13156561
#     pjba.return_value = {"foo": 14}

#     ret: int = rest_handler.get_argument("foo", default=None)

#     pjba.assert_called()
#     rhga.assert_not_called()
#     assert ret == 14


# def test_41_get_argument_args_and_body() -> None:
#     """Test `get_argument()`.

#     From Query-Args (no JSON-body arguments)
#     """
#     pjba.return_value = {}
#     rhga.return_value = 55

#     ret: int = rest_handler.get_argument("foo", default=None)

#     pjba.assert_called()
#     rhga.assert_called_with("foo", None, strip=True)
#     assert ret == 55


# def test_42_get_argument_args_and_body() -> None:
#     """Test `get_argument()`.

#     From Query-Args (with JSON & Query-Arg values) -- but only 1 match
#     """
#     pjba.return_value = {"baz": 7}
#     rhga.return_value = 90

#     ret: int = rest_handler.get_argument("foo", default=None)

#     pjba.assert_called()
#     rhga.assert_called_with("foo", None, strip=True)
#     assert ret == 90


# def test_43_get_argument_args_and_body() -> None:
#     """Test `get_argument()`.

#     From JSON-body (with JSON & Query-Arg matches) -> should grab JSON
#     """
#     pjba.return_value = {"foo": 1}
#     rhga.return_value = -8

#     ret: int = rest_handler.get_argument("foo", default=None)

#     pjba.assert_called()
#     rhga.assert_not_called()
#     assert ret == 1


# def test_44_get_argument_args_and_body() -> None:
#     """Test `get_argument()`.

#     From JSON-body (with JSON & Query-Arg matches) -> should grab JSON

#     **Test JSON-body arg type-checking**
#     """
#     pjba.return_value = {"foo": "99.9"}
#     rhga.return_value = -0.5

#     ret = rest_handler.get_argument("foo", default=None, type=str)

#     pjba.assert_called()
#     rhga.assert_not_called()
#     assert ret == "99.9"

#     # # #

#     pjba.return_value = {"foo": ["a", "bc"]}
#     rhga.return_value = "1 2 3"

#     ret2 = rest_handler.get_argument("foo", default=None, type=list)

#     pjba.assert_called()
#     rhga.assert_not_called()
#     assert ret2 == ["a", "bc"]


# def test_45_get_argument_args_and_body__errors() -> None:
#     """Test `get_argument()`.

#     **Error-Test JSON-body arg typing**

#     If there's a matching argument in JSON-body, but it's the wrong type, raise 400;
#     REGARDLESS if there's a value in the Query-Args.
#     """
#     pjba.return_value = {"foo": "NINETY-NINE"}
#     rhga.return_value = -0.5

#     with pytest.raises(tornado.web.HTTPError) as e:
#         rest_handler.get_argument("foo", default=None, type=float)
#     error_msg = (
#         "HTTP 400: `foo`: (ValueError) could not convert string to float: 'NINETY-NINE'"
#     )
#     assert str(e.value) == error_msg

#     pjba.assert_called()
#     rhga.assert_not_called()


# def test_46_get_argument_args_and_body__errors() -> None:
#     """Test `get_argument()`.

#     **Error-Test JSON-body arg choices**

#     If there's a matching argument in JSON-body, but it's not in choices
#     or it's forbidden, raise 400;
#     REGARDLESS if there's a value in the Query-Args.
#     """
#     pjba.return_value = {"foo": 5}
#     rhga.return_value = 0

#     with pytest.raises(tornado.web.HTTPError) as e:
#         rest_handler.get_argument("foo", default=None, choices=[0])
#     error_msg = "HTTP 400: `foo`: (ValueError) 5 not in choices ([0])"
#     assert str(e.value) == error_msg

#     pjba.assert_called()
#     rhga.assert_not_called()

#     # # #

#     pjba.return_value = {"foo": 5}
#     rhga.return_value = 0

#     with pytest.raises(tornado.web.HTTPError) as e:
#         rest_handler.get_argument("foo", default=None, forbiddens=[5, 6, 7])
#     error_msg = "HTTP 400: `foo`: (ValueError) 5 is forbidden ([5, 6, 7])"
#     assert str(e.value) == error_msg

#     pjba.assert_called()
#     rhga.assert_not_called()
