"""Test server/arghandler.py."""

# pylint: disable=W0212,W0621

from typing import Any
from unittest.mock import Mock, patch

import pytest  # type: ignore[import]
import tornado.web
from rest_tools.server.arghandler import ArgumentHandler, _InvalidArgumentError
from rest_tools.server.handler import RestHandler


@pytest.fixture  # type: ignore[misc]
def rest_handler() -> RestHandler:
    """Get a RestHandler instance."""
    return RestHandler(application=Mock(), request=Mock())


def test_00_cast_type() -> None:
    """Test `_cast_type()`."""
    # None - no casting
    # assert ArgumentHandler._cast_type("string", None) == "string"
    # assert ArgumentHandler._cast_type("0", None) == "0"
    # assert ArgumentHandler._cast_type("2.5", None) == "2.5"
    # str
    assert ArgumentHandler._cast_type("string", str) == "string"
    assert ArgumentHandler._cast_type("", str) == ""
    assert ArgumentHandler._cast_type(0, str) == "0"
    # int
    assert ArgumentHandler._cast_type("1", int) == 1
    assert ArgumentHandler._cast_type(1.0, int) == 1
    assert ArgumentHandler._cast_type("1", int) != "1"
    # float
    assert ArgumentHandler._cast_type("2.5", float) == 2.5
    assert ArgumentHandler._cast_type("2.0", float) == 2.0
    assert ArgumentHandler._cast_type("123", float) == 123.0
    assert ArgumentHandler._cast_type(4, float) == 4.0
    # True
    assert ArgumentHandler._cast_type("1", bool) is True
    assert ArgumentHandler._cast_type(1, bool) is True
    assert ArgumentHandler._cast_type(-99, bool) is True
    for trues in ["True", "T", "On", "Yes", "Y"]:
        for val in [
            trues.upper(),
            trues.lower(),
            trues[:-1] + trues[-1].upper(),  # upper only last char
        ]:
            assert ArgumentHandler._cast_type(val, bool) is True
    # False
    assert ArgumentHandler._cast_type("", bool) is False
    assert ArgumentHandler._cast_type("0", bool) is False
    assert ArgumentHandler._cast_type(0, bool) is False
    for falses in ["False", "F", "Off", "No", "N"]:
        for val in [
            falses.upper(),
            falses.lower(),
            falses[:-1] + falses[-1].upper(),  # upper only last char
        ]:
            assert ArgumentHandler._cast_type(val, bool) is False
    # list
    assert ArgumentHandler._cast_type("abcd", list) == ["a", "b", "c", "d"]
    assert ArgumentHandler._cast_type("", list) == []


def test_01_cast_type__errors() -> None:
    """Test `_cast_type()`."""
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._cast_type("", int)
    assert "(ValueError)" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._cast_type("", float)
    assert "(ValueError)" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._cast_type("123abc", float)
    assert "(ValueError)" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._cast_type("anything", bool)
    assert "(ValueError)" in str(e.value)


def test_02_validate_choice() -> None:
    """Test `_validate_choice()`."""
    ArgumentHandler._validate_choice("foo", None, [])
    ArgumentHandler._validate_choice("foo", None, None)

    # choices
    assert ArgumentHandler._validate_choice(True, [True, False], None) is True
    assert ArgumentHandler._validate_choice(1, [0, 1, 2], None) == 1
    assert ArgumentHandler._validate_choice("", [""], None) == ""
    ArgumentHandler._validate_choice("23", [23, "23"], None)

    # forbiddens
    ArgumentHandler._validate_choice("23", [23, "23"], [])
    ArgumentHandler._validate_choice("23", [23, "23"], ["boo!"])
    ArgumentHandler._validate_choice("23", ["23"], [23])
    ArgumentHandler._validate_choice(["list"], None, [list(), dict()])


def test_03_validate_choice__errors() -> None:
    """Test `_validate_choice()`."""
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice("23", [23], None)
    assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice("string", ["STRING"], None)
    assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice("3", [0, 1, 2], None)
    assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice("abc", [["a", "b", "c", "d"]], None)
    assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice("foo", [], [])  # no allowed choices
    assert "(ValueError)" in str(e.value) and "not in choices" in str(e.value)

    # forbiddens
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice("23", None, ["23"])
    assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice("baz", ["baz"], ["baz"])
    assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice([], None, [list(), dict()])
    assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)
    with pytest.raises(_InvalidArgumentError) as e:
        ArgumentHandler._validate_choice({}, None, [list(), dict()])
    assert "(ValueError)" in str(e.value) and "is forbidden" in str(e.value)


def test_04_cast_type() -> None:
    """Test `_cast_type()`."""
    vals = [
        "abcdefghijklmopqrstuvwxyz",
        1,
        None,
        ["this is", "a list"],
        "",
        2.5,
        {"but this": "is a dict"},
    ]

    def agreeable_type(typ: Any, val: Any) -> bool:
        if val is None:
            return False
        try:
            typ(val)
            return True
        except Exception:
            return False

    for val in vals:
        print(val)
        # Passing Cases:
        # assert val == ArgumentHandler._cast_type(val, None)  # None is always allowed
        for o_type in [type(o) for o in vals if agreeable_type(type(o), val)]:
            print(o_type)
            out = ArgumentHandler._cast_type(val, o_type)
            assert isinstance(out, o_type)

        # Error Cases:

        # None is not allowed
        if val is not None:
            with pytest.raises(_InvalidArgumentError):
                ArgumentHandler._cast_type(None, type(val))
            with pytest.raises(ValueError):
                ArgumentHandler._cast_type(None, type(val), server_side_error=True)

        # type-mismatch  # pylint: disable=C0123
        for o_type in [type(o) for o in vals if not agreeable_type(type(o), val)]:
            print(o_type)
            with pytest.raises(_InvalidArgumentError):
                ArgumentHandler._cast_type(val, o_type)
            with pytest.raises((ValueError, TypeError)):
                ArgumentHandler._cast_type(val, o_type, server_side_error=True)


def test_05_strict_type() -> None:
    """Test `_cast_type(strict_type=True)`."""
    bad_vals = {
        str: [1, [], False],
        bool: [1, "True", [], [False]],
        int: [2.1, 9.0, "10", [], [5]],
        list: ["not a list", {"a": 1}, 1],
        float: [2, "1e4", [], [1.0]],
    }

    for o_type, values in bad_vals.items():
        for val in values:
            with pytest.raises(_InvalidArgumentError):
                ArgumentHandler._cast_type(val, o_type, strict_type=True)
            with pytest.raises((ValueError, TypeError)):
                ArgumentHandler._cast_type(
                    val, o_type, strict_type=True, server_side_error=True
                )


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_10_default(rhga: Mock, pjba: Mock, rest_handler: RestHandler) -> None:
    """Test cases where just the default is returned.

    NOTE: RequestHandler.get_argument() always returns the default if the arg is absent.
    """
    default: Any
    for default in [None, "string", 100, 50.5]:
        print(default)
        pjba.return_value = {}
        rhga.return_value = default
        assert default == rest_handler.get_argument("arg", default=default)

    # w/ typing
    for default in ["string", 100, 50.5]:
        print(default)
        pjba.return_value = {}
        rhga.return_value = default
        ret = rest_handler.get_argument("arg", type=type(default), default=default)
        assert ret == default


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_20_get_argument_no_body(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `request.arguments`/`RequestHandler.get_argument()` arguments.

    No tests for body-parsing.
    """
    args = {
        "foo": ("-10", int),
        "bar": ("True", bool),
        "bat": ("2.5", float),
        "baz": ("Toyota Corolla", str),
        "boo": ("False", bool),
    }

    for arg, (val, type_) in args.items():
        # pylint: disable=E1102
        print(arg)
        print(val)
        print(type_)
        # w/o typing
        pjba.return_value = {}
        rhga.return_value = val
        assert val == rest_handler.get_argument(arg, default=None)
        # w/ typing
        pjba.return_value = {}
        rhga.return_value = val
        ret = rest_handler.get_argument(arg, default=None, type=type_)  # type: ignore  # dynamic types aren't real-world issues
        assert ret == type_(val) or (val == "False" and ret is False and type_ == bool)

    # NOTE - `default` non-error use-cases solely on RequestHandler.get_argument(), so no tests
    # NOTE - `strip` use-cases depend solely on RequestHandler.get_argument(), so no tests
    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_21_get_argument_no_body__errors(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `request.arguments`/`RequestHandler.get_argument()` arguments.

    No tests for body-parsing.
    """
    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        pjba.return_value = {}
        rhga.side_effect = tornado.web.MissingArgumentError("Reqd")
        rest_handler.get_argument("Reqd")
    error_msg = "HTTP 400: `Reqd`: (MissingArgumentError) required argument is missing"
    assert str(e.value) == error_msg

    # NOTE - `type_` and `choices` are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
def test_30_get_json_body_argument(pjba: Mock, rest_handler: RestHandler) -> None:
    """Test `request.body` JSON arguments."""
    body = {"green": 10, "eggs": True, "and": "wait for it...", "ham": [1, 2, 4]}

    # Simple Use Cases
    for arg, val in body.items():
        print(arg)
        pjba.return_value = body
        assert val == rest_handler.get_json_body_argument(arg)

    # Default Use Cases
    for arg, val in body.items():
        print(arg)
        pjba.return_value = {a: v for a, v in body.items() if a != arg}
        assert "Terry" == rest_handler.get_json_body_argument(arg, default="Terry")

    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
def test_31_get_json_body_argument__errors(
    pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `request.body` JSON arguments."""
    body = {"green": 10, "eggs": True, "and": "wait for it...", "ham": [1, 2, 4]}

    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        pjba.return_value = body
        rest_handler.get_json_body_argument("Reqd")
    error_msg = "HTTP 400: `Reqd`: (MissingArgumentError) required argument is missing"
    assert str(e.value) == error_msg

    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
def test_32_get_json_body_argument_typechecking(
    pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_json_body_argument()`.

    **Test JSON-body arg type-checking**
    """
    pjba.return_value = {"foo": "99.9"}

    ret = rest_handler.get_json_body_argument("foo", default=None, type=str)

    pjba.assert_called()
    assert ret == "99.9"

    # # #

    pjba.return_value = {"foo": ["a", "bc"]}

    ret2 = rest_handler.get_json_body_argument("foo", default=None, type=list)

    pjba.assert_called()
    assert ret2 == ["a", "bc"]


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
def test_33_get_json_body_argument_typechecking__errors(
    pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_json_body_argument()`.

    If there's a matching argument in JSON-body, but it's the wrong
    type, raise 400.
    """
    pjba.return_value = {"foo": "NINETY-NINE"}

    with pytest.raises(tornado.web.HTTPError) as e:
        rest_handler.get_json_body_argument("foo", default=None, type=float)
    error_msg = (
        "HTTP 400: `foo`: (ValueError) could not convert string to float: 'NINETY-NINE'"
    )
    assert str(e.value) == error_msg

    pjba.assert_called()


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_40_get_argument_args_and_body(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_argument()`.

    From JSON-body (no Query-Args)
    """
    # TODO - patch based on argument: https://stackoverflow.com/a/16162316/13156561
    pjba.return_value = {"foo": 14}

    ret: int = rest_handler.get_argument("foo", default=None)

    pjba.assert_called()
    rhga.assert_not_called()
    assert ret == 14


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_41_get_argument_args_and_body(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_argument()`.

    From Query-Args (no JSON-body arguments)
    """
    pjba.return_value = {}
    rhga.return_value = 55

    ret: int = rest_handler.get_argument("foo", default=None)

    pjba.assert_called()
    rhga.assert_called_with("foo", None, strip=True)
    assert ret == 55


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_42_get_argument_args_and_body(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_argument()`.

    From Query-Args (with JSON & Query-Arg values) -- but only 1 match
    """
    pjba.return_value = {"baz": 7}
    rhga.return_value = 90

    ret: int = rest_handler.get_argument("foo", default=None)

    pjba.assert_called()
    rhga.assert_called_with("foo", None, strip=True)
    assert ret == 90


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_43_get_argument_args_and_body(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_argument()`.

    From JSON-body (with JSON & Query-Arg matches) -> should grab JSON
    """
    pjba.return_value = {"foo": 1}
    rhga.return_value = -8

    ret: int = rest_handler.get_argument("foo", default=None)

    pjba.assert_called()
    rhga.assert_not_called()
    assert ret == 1


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_44_get_argument_args_and_body(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_argument()`.

    From JSON-body (with JSON & Query-Arg matches) -> should grab JSON

    **Test JSON-body arg type-checking**
    """
    pjba.return_value = {"foo": "99.9"}
    rhga.return_value = -0.5

    ret = rest_handler.get_argument("foo", default=None, type=str)

    pjba.assert_called()
    rhga.assert_not_called()
    assert ret == "99.9"

    # # #

    pjba.return_value = {"foo": ["a", "bc"]}
    rhga.return_value = "1 2 3"

    ret2 = rest_handler.get_argument("foo", default=None, type=list)

    pjba.assert_called()
    rhga.assert_not_called()
    assert ret2 == ["a", "bc"]


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_45_get_argument_args_and_body__errors(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_argument()`.

    **Error-Test JSON-body arg typing**

    If there's a matching argument in JSON-body, but it's the wrong type, raise 400;
    REGARDLESS if there's a value in the Query-Args.
    """
    pjba.return_value = {"foo": "NINETY-NINE"}
    rhga.return_value = -0.5

    with pytest.raises(tornado.web.HTTPError) as e:
        rest_handler.get_argument("foo", default=None, type=float)
    error_msg = (
        "HTTP 400: `foo`: (ValueError) could not convert string to float: 'NINETY-NINE'"
    )
    assert str(e.value) == error_msg

    pjba.assert_called()
    rhga.assert_not_called()


@patch("rest_tools.server.arghandler._parse_json_body_arguments")
@patch("tornado.web.RequestHandler.get_argument")
def test_46_get_argument_args_and_body__errors(
    rhga: Mock, pjba: Mock, rest_handler: RestHandler
) -> None:
    """Test `get_argument()`.

    **Error-Test JSON-body arg choices**

    If there's a matching argument in JSON-body, but it's not in choices
    or it's forbidden, raise 400;
    REGARDLESS if there's a value in the Query-Args.
    """
    pjba.return_value = {"foo": 5}
    rhga.return_value = 0

    with pytest.raises(tornado.web.HTTPError) as e:
        rest_handler.get_argument("foo", default=None, choices=[0])
    error_msg = "HTTP 400: `foo`: (ValueError) 5 not in choices ([0])"
    assert str(e.value) == error_msg

    pjba.assert_called()
    rhga.assert_not_called()

    # # #

    pjba.return_value = {"foo": 5}
    rhga.return_value = 0

    with pytest.raises(tornado.web.HTTPError) as e:
        rest_handler.get_argument("foo", default=None, forbiddens=[5, 6, 7])
    error_msg = "HTTP 400: `foo`: (ValueError) 5 is forbidden ([5, 6, 7])"
    assert str(e.value) == error_msg

    pjba.assert_called()
    rhga.assert_not_called()
