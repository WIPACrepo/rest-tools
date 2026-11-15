"""Test RestHandler error responses, including multi-line reasons (issue #217)."""

import socket
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
import requests
import tornado.web

from rest_tools.client import RestClient
from rest_tools.server import RestHandler, RestServer


@pytest.fixture
def port() -> int:
    """Get an ephemeral port number."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    ephemeral_port = s.getsockname()[1]
    s.close()
    return ephemeral_port


@pytest_asyncio.fixture
async def server(port: int) -> AsyncIterator[Callable[[], RestClient]]:
    """Start up a REST server with handlers that produce various errors."""
    rs = RestServer(debug=True)

    class RaiseHandler(RestHandler):
        """Raise HTTPError with the reason given in the JSON body."""

        async def post(self) -> None:  # ty: ignore[incompatible-mutable-override]
            reason = self.get_argument("reason", None)
            raise tornado.web.HTTPError(400, reason=reason)

    class SendErrorHandler(RestHandler):
        """Call send_error() with the reason as a keyword."""

        async def post(self) -> None:  # ty: ignore[incompatible-mutable-override]
            self.send_error(400, reason=self.get_argument("reason"))

    class DirectStatusHandler(RestHandler):
        """Set a multi-line status directly and write a custom body."""

        async def post(self) -> None:  # ty: ignore[incompatible-mutable-override]
            self.set_status(400, reason=self.get_argument("reason"))
            self.write({"custom": True})

    class PrepareErrorHandler(RestHandler):
        """Raise a multi-line error from prepare()."""

        def prepare(self) -> None:
            super().prepare()
            raise tornado.web.HTTPError(403, reason="denied\nbecause reasons")

        async def get(self) -> None:  # ty: ignore[incompatible-mutable-override]
            self.write({})

    rs.add_route("/raise", RaiseHandler)
    rs.add_route("/send-error", SendErrorHandler)
    rs.add_route("/direct", DirectStatusHandler)
    rs.add_route("/prepare", PrepareErrorHandler)
    rs.startup(address="localhost", port=port)

    def client() -> RestClient:
        return RestClient(f"http://localhost:{port}", retries=0)

    try:
        yield client
    finally:
        await rs.stop()


async def _request_error(
    rc: RestClient, method: str, path: str, args: dict | None = None
) -> requests.Response:
    """Make a request expected to fail; return the error response."""
    with pytest.raises(requests.exceptions.HTTPError) as e:
        await rc.request(method, path, args)
    return e.value.response


@pytest.mark.parametrize(
    "reason",
    [
        "line one\nline two",
        "line one\r\nline two",
        "line one\rline two",
        "line one\nline two\nline three",
    ],
)
async def test_multiline_reason(server: Callable[[], RestClient], reason: str) -> None:
    """Status line gets the first line; JSON body gets the full text."""
    resp = await _request_error(server(), "POST", "/raise", {"reason": reason})
    assert resp.status_code == 400
    assert resp.reason == "line one"
    assert resp.json() == {"code": 400, "error": reason}


async def test_single_line_reason(server: Callable[[], RestClient]) -> None:
    """Single-line reasons are unchanged."""
    resp = await _request_error(server(), "POST", "/raise", {"reason": "bad input"})
    assert resp.status_code == 400
    assert resp.reason == "bad input"
    assert resp.json() == {"code": 400, "error": "bad input"}


async def test_no_reason(server: Callable[[], RestClient]) -> None:
    """No reason -> Tornado's default phrase in both places."""
    resp = await _request_error(server(), "POST", "/raise")
    assert resp.status_code == 400
    assert resp.reason == "Bad Request"
    assert resp.json() == {"code": 400, "error": "Bad Request"}


@pytest.mark.parametrize("reason", ["\n", "\r\n\n", " \n "])
async def test_line_break_only_reason(
    server: Callable[[], RestClient], reason: str
) -> None:
    """Reason of only line breaks/whitespace -> default phrase."""
    resp = await _request_error(server(), "POST", "/raise", {"reason": reason})
    assert resp.status_code == 400
    assert "\n" not in resp.reason and "\r" not in resp.reason
    assert resp.json() == {"code": 400, "error": "Bad Request"}


async def test_send_error_reason(server: Callable[[], RestClient]) -> None:
    """send_error(reason=...) keeps the full text in the body."""
    reason = "first\nsecond"
    resp = await _request_error(server(), "POST", "/send-error", {"reason": reason})
    assert resp.status_code == 400
    assert resp.reason == "first"
    assert resp.json() == {"code": 400, "error": reason}


async def test_direct_set_status(server: Callable[[], RestClient]) -> None:
    """Direct set_status() with a multi-line reason still sends a response."""
    resp = await _request_error(server(), "POST", "/direct", {"reason": "a\nb"})
    assert resp.status_code == 400
    assert resp.reason == "a"
    assert resp.json() == {"custom": True}


async def test_prepare_error(server: Callable[[], RestClient]) -> None:
    """Multi-line errors raised from prepare() are handled too."""
    resp = await _request_error(server(), "GET", "/prepare")
    assert resp.status_code == 403
    assert resp.reason == "denied"
    assert resp.json() == {"code": 403, "error": "denied\nbecause reasons"}
