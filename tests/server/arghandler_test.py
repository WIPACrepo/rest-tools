"""Test server/arghandler.py."""

# pylint: disable=W0212

import pytest
import tornado.web

# local imports
from rest_tools.server.arghandler import ArgumentHandler


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
    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler._qualify_argument(int, [], "")
    assert "(ValueError)" in str(e.value)
    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler._qualify_argument(float, [], "")
    assert "(ValueError)" in str(e.value)
    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler._qualify_argument(float, [], "123abc")
    assert "(ValueError)" in str(e.value)

    # Test Choices:
    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler._qualify_argument(None, [23], "23")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)
    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler._qualify_argument(str, ["STRING"], "string")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)
    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler._qualify_argument(int, [0, 1, 2], "3")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)
    with pytest.raises(tornado.web.HTTPError) as e:
        ArgumentHandler._qualify_argument(list, [["a", "b", "c", "d"]], "abc")
    assert "(ValueError)" in str(e.value) and "not in options" in str(e.value)


def test_10_type_check() -> None:
    """Test `_type_check()`."""
    pass


def test_20_get_argument_no_body() -> None:
    """Test `request.arguments`/`RequestHandler.get_argument()` arguments.

    No tests for body-parsing.
    """
    pass


def test_21_get_argument_no_body() -> None:
    """Test `request.arguments`/`RequestHandler.get_argument()` arguments.

    No tests for body-parsing.
    """
    pass


def test_30_get_json_body_argument() -> None:
    """Test `request.body` JSON arguments."""
    pass


def test_31_get_json_body_argument() -> None:
    """Test `request.body` JSON arguments."""
    pass


def test_40_get_argument_args_and_body() -> None:
    """Test `get_argument()`."""
    pass


def test_41_get_argument_args_and_body() -> None:
    """Test `get_argument()`."""
    pass
