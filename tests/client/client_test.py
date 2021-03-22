"""Test script for RestClient."""


import logging
import signal
import sys
from contextlib import contextmanager
from unittest.mock import Mock

import pytest
import requests  # TODO - remove
from httpretty import HTTPretty, httprettified  # type: ignore[import]
from requests import PreparedRequest
from requests.exceptions import SSLError, Timeout
from sure import expect  # type: ignore[import]

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
    response_stream = [
        b'{"foo-bar":"baz"}\r\n',
        b"\r\n",
        b'{"green":["eggs", "and", "ham"]}\r\n',
    ]

    # ----------------------------------------------------------------------------------

    HTTPretty.register_uri(
        HTTPretty.POST, mock_url, body=(ln for ln in response_stream), streaming=True,
    )

    # taken from the requests docs

    # test iterating by line
    # http://docs.python-requests.org/en/latest/user/advanced/#streaming-requests
    response = requests.post(
        mock_url,
        data={"track": "requests"},
        auth=("username", "password"),
        stream=True,
    )

    line_iter = response.iter_lines()
    with _in_time(0.01, "Iterating by line is taking forever!"):
        for i, _ in enumerate(response_stream):
            # pylint: disable=E1101
            expect(next(line_iter).strip()).to.equal(response_stream[i].strip())

    # ----------------------------------------------------------------------------------

    HTTPretty.register_uri(
        HTTPretty.POST, mock_url, body=(ln for ln in response_stream), streaming=True,
    )
    # test iterating by line after a second request
    response = requests.post(
        mock_url,
        data={"track": "requests"},
        auth=("username", "password"),
        stream=True,
    )

    line_iter = response.iter_lines()
    with _in_time(
        0.01, "Iterating by line is taking forever the second time " "around!"
    ):
        for i, _ in enumerate(response_stream):
            # pylint: disable=E1101
            expect(next(line_iter).strip()).to.equal(response_stream[i].strip())

    # ----------------------------------------------------------------------------------

    HTTPretty.register_uri(
        HTTPretty.POST, mock_url, body=(ln for ln in response_stream), streaming=True,
    )
    # test iterating by char
    response = requests.post(
        mock_url,
        data={"track": "requests"},
        auth=("username", "password"),
        stream=True,
    )

    twitter_expected_response_body = b"".join(response_stream)
    with _in_time(0.02, "Iterating by char is taking forever!"):
        twitter_body = b"".join(c for c in response.iter_content(chunk_size=1))

    # pylint: disable=E1101
    expect(twitter_body).to.equal(twitter_expected_response_body)

    # ----------------------------------------------------------------------------------

    # test iterating by chunks larger than the stream
    HTTPretty.register_uri(
        HTTPretty.POST, mock_url, body=(ln for ln in response_stream), streaming=True,
    )
    response = requests.post(
        mock_url,
        data={"track": "requests"},
        auth=("username", "password"),
        stream=True,
    )

    with _in_time(0.02, "Iterating by large chunks is taking forever!"):
        twitter_body = b"".join(c for c in response.iter_content(chunk_size=1024))

    # pylint: disable=E1101
    expect(twitter_body).to.equal(twitter_expected_response_body)
