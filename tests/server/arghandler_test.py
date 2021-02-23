"""Test server/arghandler.py."""

# pylint: disable=W0212

from unittest.mock import ANY, Mock, patch

import pytest
import tornado.web

# local imports
from rest_tools.server.arghandler import (
    _UnqualifiedArgumentError,
    ArgumentHandler,
    NO_DEFAULT,
)


def test_00_qualify_argument() -> None:
    """Test `_qualify_argument()`."""
    # Test Types:
    # None - no casting
    assert ArgumentHandler._qualify_argument(None, [], "string") == "string"
    assert ArgumentHandler._qualify_argument(None, [], "0") == "0"
    assert ArgumentHandler._qualify_argument(None, [], "2.5") == "2.5"
    # str
    assert ArgumentHandler._qualify_argument(str, [], "string") == "string"
    assert ArgumentHandler._qualify_argument(str, [], "") == ""
    assert ArgumentHandler._qualify_argument(str, [], 0) == "0"
    # int
    assert ArgumentHandler._qualify_argument(int, [], "1") == 1
    assert ArgumentHandler._qualify_argument(int, [], "1") != "1"
    # float
    assert ArgumentHandler._qualify_argument(float, [], "2.5") == 2.5
    # True
    assert ArgumentHandler._qualify_argument(bool, [], "True") is True
    assert ArgumentHandler._qualify_argument(bool, [], "1") is True
    assert ArgumentHandler._qualify_argument(bool, [], 1) is True
    assert ArgumentHandler._qualify_argument(bool, [], "anything") is True
    # False
    assert ArgumentHandler._qualify_argument(bool, [], "") is False
    assert ArgumentHandler._qualify_argument(bool, [], None) is False
    for val in ["FALSE", "False", "false", "0", 0, "NO", "No", "no"]:
        assert ArgumentHandler._qualify_argument(bool, [], val) is False
    # list
    assert ArgumentHandler._qualify_argument(list, [], "abcd") == ["a", "b", "c", "d"]
    assert ArgumentHandler._qualify_argument(list, [], "") == []

    # Test Choices:
    assert ArgumentHandler._qualify_argument(bool, [True], "anything") is True
    assert ArgumentHandler._qualify_argument(int, [0, 1, 2], "1") == 1
    assert ArgumentHandler._qualify_argument(None, [""], "") == ""
    ArgumentHandler._qualify_argument(None, [23, "23"], "23")


def test_01_qualify_argument_errors() -> None:
    """Test `_qualify_argument()`."""
    # Test Types:
    with pytest.raises(_UnqualifiedArgumentError) as e:
        ArgumentHandler._qualify_argument(int, [], "")
    assert "(ValueError)" in str(e.value)
    with pytest.raises(_UnqualifiedArgumentError) as e:
        ArgumentHandler._qualify_argument(float, [], "")
    assert "(ValueError)" in str(e.value)
    with pytest.raises(_UnqualifiedArgumentError) as e:
        ArgumentHandler._qualify_argument(float, [], "123abc")
    assert "(ValueError)" in str(e.value)

    # Test Choices:
    with pytest.raises(_UnqualifiedArgumentError) as e:
        ArgumentHandler._qualify_argument(None, [23], "23")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)
    with pytest.raises(_UnqualifiedArgumentError) as e:
        ArgumentHandler._qualify_argument(str, ["STRING"], "string")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)
    with pytest.raises(_UnqualifiedArgumentError) as e:
        ArgumentHandler._qualify_argument(int, [0, 1, 2], "3")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)
    with pytest.raises(_UnqualifiedArgumentError) as e:
        ArgumentHandler._qualify_argument(list, [["a", "b", "c", "d"]], "abc")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)


def test_10_type_check() -> None:
    """Test `_type_check()`."""
    vals = [
        "abcdef",
        1,
        None,
        ["this is", "a list"],
        "",
        2.5,
        {"but this": "is a dict"},
    ]

    for val in vals:
        print(val)
        # Passing Cases
        ArgumentHandler._type_check(type(val), val)
        ArgumentHandler._type_check(None, val)  # type_ == None is always allowed

        # Error Cases # pylint: disable=C0123
        if val is None:  # val == None is always allowed
            continue
        for o_type in [type(o) for o in vals if type(o) != type(val)]:
            print(o_type)
            with pytest.raises(ValueError):
                ArgumentHandler._type_check(o_type, val)


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_20_get_argument_no_body(twrh: Mock, gjb: Mock) -> None:
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
        gjb.return_value = {}
        twrh.get_argument.return_value = val
        ret = ArgumentHandler.get_argument(twrh, arg, None, False, None, [])
        assert ret == val
        # w/ typing
        gjb.return_value = {}
        twrh.get_argument.return_value = val
        ret = ArgumentHandler.get_argument(twrh, arg, None, False, type_, [])
        assert ret == type_(val) or (val == "False" and ret is False and type_ == bool)

    # NOTE - `default` non-error use-cases solely on RequestHandler.get_argument(), so no tests
    # NOTE - `strip` use-cases depend solely on RequestHandler.get_argument(), so no tests
    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_21_get_argument_no_body_errors(twrh: Mock, gjb: Mock) -> None:
    """Test `request.arguments`/`RequestHandler.get_argument()` arguments.

    No tests for body-parsing.
    """
    # Missing Required Argument
    with pytest.raises(tornado.web.HTTPError) as e:
        gjb.return_value = {}
        twrh.get_argument.side_effect = tornado.web.MissingArgumentError("Reqd")
        ArgumentHandler.get_argument(twrh, "Reqd", NO_DEFAULT, False, None, [])
    assert "Reqd" in str(e.value)
    assert "400" in str(e.value)

    # NOTE - `type_` and `choices` are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._get_json_body")
def test_30_get_json_body_argument(gjb: Mock) -> None:
    """Test `request.body` JSON arguments."""
    body = {"green": 10, "eggs": True, "and": "wait for it...", "ham": [1, 2, 4]}

    # Simple Use Cases
    for arg, val in body.items():
        gjb.return_value = body
        ret = ArgumentHandler.get_json_body_argument(ANY, arg, None, [])
        assert ret == val

    # Default Use Cases
    for arg, val in body.items():
        gjb.return_value = {a: v for a, v in body.items() if a != arg}
        ret = ArgumentHandler.get_json_body_argument(ANY, arg, "Terry", [])
        assert ret == "Terry"

    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._get_json_body")
def test_31_get_json_body_argument_errors(gjb: Mock) -> None:
    """Test `request.body` JSON arguments."""
    body = {"green": 10, "eggs": True, "and": "wait for it...", "ham": [1, 2, 4]}

    # Missing Required Argument
    with pytest.raises(tornado.web.MissingArgumentError) as e:
        gjb.return_value = body
        ArgumentHandler.get_json_body_argument(ANY, "Reqd", NO_DEFAULT, [])
    assert "Reqd" in str(e.value)

    # NOTE - `choices` use-cases are tested in `_qualify_argument` tests


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_40_get_argument_args_and_body(twrh: Mock, gjb: Mock) -> None:
    """Test `get_argument()`.

    From JSON-body (no Query-Args)
    """
    # TODO - patch based on argument: https://stackoverflow.com/a/16162316/13156561
    gjb.return_value = {"foo": 14}

    ret = ArgumentHandler.get_argument(twrh, "foo", None, False, None, [])

    gjb.assert_called_with(twrh)
    twrh.get_argument.assert_not_called()
    assert ret == 14


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_41_get_argument_args_and_body(twrh: Mock, gjb: Mock) -> None:
    """Test `get_argument()`.

    From Query-Args (no JSON-body arguments)
    """
    gjb.return_value = {}
    twrh.get_argument.return_value = 55

    ret = ArgumentHandler.get_argument(twrh, "foo", None, False, None, [])

    gjb.assert_called_with(twrh)
    twrh.get_argument.assert_called_with("foo", None, strip=False)
    assert ret == 55


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_42_get_argument_args_and_body(twrh: Mock, gjb: Mock) -> None:
    """Test `get_argument()`.

    From Query-Args (with JSON & Query-Arg values) -- but only 1 match
    """
    gjb.return_value = {"baz": 7}
    twrh.get_argument.return_value = 90

    ret = ArgumentHandler.get_argument(twrh, "foo", None, False, None, [])

    gjb.assert_called_with(twrh)
    twrh.get_argument.assert_called_with("foo", None, strip=False)
    assert ret == 90


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_43_get_argument_args_and_body(twrh: Mock, gjb: Mock) -> None:
    """Test `get_argument()`.

    From JSON-body (with JSON & Query-Arg matches) -> should grab JSON
    """
    gjb.return_value = {"foo": 1}
    twrh.get_argument.return_value = -8

    ret = ArgumentHandler.get_argument(twrh, "foo", None, False, None, [])

    gjb.assert_called_with(twrh)
    twrh.get_argument.assert_not_called()
    assert ret == 1


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_44_get_argument_args_and_body(twrh: Mock, gjb: Mock) -> None:
    """Test `get_argument()`.

    From JSON-body (with JSON & Query-Arg matches) -> should grab JSON

    **Test JSON-body arg typing**
    """
    gjb.return_value = {"foo": "99"}
    twrh.get_argument.return_value = -0.5

    ret = ArgumentHandler.get_argument(twrh, "foo", None, False, int, [])

    gjb.assert_called_with(twrh)
    twrh.get_argument.assert_not_called()
    assert ret == 99


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_45_get_argument_args_and_body_errors(twrh: Mock, gjb: Mock) -> None:
    """Test `get_argument()`.

    **Error-Test JSON-body arg typing**

    If there's a matching argument in JSON-body, but it's the wrong type, raise 400;
    REGARDLESS if there's a value in the Query-Args.
    """
    gjb.return_value = {"foo": "NINETY-NINE"}
    twrh.get_argument.return_value = -0.5

    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler.get_argument(twrh, "foo", None, False, int, [])
    assert "(ValueError)" in str(e.value)
    assert "400" in str(e.value)
    assert "NINETY-NINE" in str(e.value)
    assert "foo" in str(e.value)

    gjb.assert_called_with(twrh)
    twrh.get_argument.assert_not_called()


@patch("rest_tools.server.arghandler._get_json_body")
@patch("tornado.web.RequestHandler")
def test_46_get_argument_args_and_body_errors(twrh: Mock, gjb: Mock) -> None:
    """Test `get_argument()`.

    **Error-Test JSON-body arg choices**

    If there's a matching argument in JSON-body, but it's not in choices, raise 400;
    REGARDLESS if there's a value in the Query-Args.
    """
    gjb.return_value = {"foo": 5}
    twrh.get_argument.return_value = 0

    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler.get_argument(twrh, "foo", None, False, None, ["this one!"])
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)
    assert "400" in str(e.value)
    assert "foo" in str(e.value)

    gjb.assert_called_with(twrh)
    twrh.get_argument.assert_not_called()
