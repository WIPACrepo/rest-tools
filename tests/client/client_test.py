"""Test script for RestClient."""


import json
import logging
import signal
import sys
from contextlib import contextmanager
from typing import Any
from unittest.mock import Mock

import pytest
import requests  # TODO - remove
from httpretty import HTTPretty, httprettified  # type: ignore[import]
from requests import PreparedRequest
from requests.exceptions import SSLError, Timeout

sys.path.append(".")
from rest_tools.client import RestClient  # isort:skip # noqa # pylint: disable=C0413
from rest_tools.utils.json_util import (  # isort:skip # noqa # pylint: disable=C0413
    json_decode,
    json_encode,
)

logger = logging.getLogger("rest_client")


def test_01_init() -> None:
    """Test `__init__()` & `close()`."""
    rpc = RestClient("http://test", "passkey")
    rpc.close()


@pytest.mark.asyncio  # type: ignore[misc]
async def test_10_request(requests_mock: Mock) -> None:
    """Test `async request()`."""
    result = {"result": "the result"}
    rpc = RestClient("http://test", "passkey", timeout=0.1)

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        _ = json_decode(req.body)
        return json_encode(result).encode("utf-8")

    requests_mock.post("/test", content=response)
    ret = await rpc.request("POST", "test", {})

    assert requests_mock.called
    assert ret == result

    result2 = {"result2": "the result 2"}

    def response2(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        _ = json_decode(req.body)
        return json_encode(result2).encode("utf-8")

    requests_mock.post("/test2", content=response2)
    ret = await rpc.request("POST", "/test2")

    assert requests_mock.called
    assert ret == result2


@pytest.mark.asyncio  # type: ignore[misc]
async def test_11_request(requests_mock: Mock) -> None:
    """Test request in `async request()`."""
    rpc = RestClient("http://test", "passkey", timeout=0.1)
    requests_mock.get("/test", content=b"")
    ret = await rpc.request("GET", "test", {})

    assert requests_mock.called
    assert ret is None


@pytest.mark.asyncio  # type: ignore[misc]
async def test_20_timeout(requests_mock: Mock) -> None:
    """Test timeout in `async request()`."""
    rpc = RestClient("http://test", "passkey", timeout=0.1, backoff=False)
    requests_mock.post("/test", exc=Timeout)

    with pytest.raises(Timeout):
        _ = await rpc.request("POST", "test", {})


@pytest.mark.asyncio  # type: ignore[misc]
async def test_21_ssl_error(requests_mock: Mock) -> None:
    """Test ssl error in `async request()`."""
    rpc = RestClient("http://test", "passkey", timeout=0.1, backoff=False)
    requests_mock.post("/test", exc=SSLError)

    with pytest.raises(SSLError):
        _ = await rpc.request("POST", "test", {})


@pytest.mark.asyncio  # type: ignore[misc]
async def test_22_request(requests_mock: Mock) -> None:
    """Test `async request()`."""
    rpc = RestClient("http://test", "passkey", timeout=0.1)
    requests_mock.get("/test", content=b'{"foo"}')

    with pytest.raises(Exception):
        _ = await rpc.request("GET", "test", {})


def test_90_request_seq(requests_mock: Mock) -> None:
    """Test `request_seq()`."""
    result = {"result": "the result"}
    rpc = RestClient("http://test", "passkey", timeout=0.1)

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        _ = json_decode(req.body)
        return json_encode(result).encode("utf-8")

    requests_mock.post("/test", content=response)
    ret = rpc.request_seq("POST", "test", {})

    assert requests_mock.called
    assert ret == result


@pytest.mark.asyncio  # type: ignore[misc]
async def test_91_request_seq(requests_mock: Mock) -> None:
    """Test `request_seq()`."""
    result = {"result": "the result"}
    rpc = RestClient("http://test", "passkey", timeout=0.1)

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        _ = json_decode(req.body)
        return json_encode(result).encode("utf-8")

    requests_mock.post("/test", content=response)
    ret = rpc.request_seq("POST", "test", {})

    assert requests_mock.called
    assert ret == result


@pytest.mark.asyncio  # type: ignore[misc]  # type: ignore[misc]
async def test_92_request_seq(requests_mock: Mock) -> None:
    """Test `request_seq()`."""
    rpc = RestClient("http://test", "passkey", timeout=0.1)

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        raise Exception()

    requests_mock.post("/test", content=response)

    with pytest.raises(Exception):
        rpc.request_seq("POST", "test", {})


@contextmanager
def _in_time(time, message):  # type: ignore[no-untyped-def]
    # Based on https://github.com/gabrielfalcao/HTTPretty/blob/master/tests/functional/test_requests.py#L290."""
    # A context manager that uses signals to force a time limit in tests
    # (unlike the `@within` decorator, which only complains afterward), or
    # raise an AssertionError.

    def handler(signum, frame):  # type: ignore[no-untyped-def]
        raise AssertionError(message)

    signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, time)
    yield
    signal.setitimer(signal.ITIMER_REAL, 0)


@httprettified  # type: ignore[misc]
def test_100_request_stream() -> None:
    """Test `request_stream()`.

    Based on https://github.com/gabrielfalcao/HTTPretty/blob/master/tests/functional/test_requests.py#L290
    """
    mock_url = "http://stream.test"
    expected_stream = [
        b'{"foo-bar":"baz"}\r\n',
        b"\r\n",
        b'{"green":["eggs", "and", "ham"]}\r\n',
        b'{"george": 1, "paul": 2, "ringo": 3, "john": 4}\n',
        b'"this is just a string"\n',
        b"[1,2,3]\n",
    ]
    rpc = RestClient(mock_url, "passkey", timeout=1)

    def jsonify(val: bytes) -> Any:
        return json.loads(val.strip()) if val.strip() else None

    # test multiple times
    for test_num in range(2):
        print(f"\niteration #{test_num}")
        HTTPretty.register_uri(
            HTTPretty.POST,
            mock_url + "/foo/bar/",
            body=(ln for ln in expected_stream),
            streaming=True,
        )
        response_stream = rpc.request_stream("POST", "/foo/bar/", {})

        with _in_time(0.01, "Iterating by line is taking forever!"):
            for i, resp in enumerate(response_stream):
                print(f"{resp=}")
                assert resp == jsonify(expected_stream[i])

    # now w/ chunk sizes
    for chunk_size in [None, 8, 0, -1, 1024, 32768]:
        print(f"\nchunk_size: {chunk_size}")
        HTTPretty.register_uri(
            HTTPretty.POST,
            mock_url + "/foo/bar/",
            body=(ln for ln in expected_stream),
            streaming=True,
        )
        response_stream = rpc.request_stream(
            "POST", "/foo/bar/", {}, chunk_size=chunk_size
        )

        with _in_time(0.01, "Iterating by line is taking forever w/ chunks!"):
            for i, resp in enumerate(response_stream):
                print(f"{resp=}")
                assert resp == jsonify(expected_stream[i])
