"""Integration test fixtures."""

import socket
from typing import AsyncIterator, Callable

import pytest
import pytest_asyncio
import tornado
from tornado.web import RequestHandler

from rest_tools.client import RestClient
from rest_tools.server import RestServer, RestHandler


@pytest.fixture
def port() -> int:
    """Get an ephemeral port number."""
    # unix.stackexchange.com/a/132524
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    addr = s.getsockname()
    ephemeral_port = addr[1]
    s.close()
    return ephemeral_port

class TestHandler(RestHandler):
    ROUTE = "/echo/this"

    async def post(self) -> None:
        self.write({})
        # if self.get_argument("raise", None):
        #     raise tornado.web.HTTPError(400, self.get_argument("raise"))
        # self.write(self.get_argument("echo", {}))
@pytest_asyncio.fixture
async def server(port: int) -> AsyncIterator[Callable[[], RestClient]]:
    """Start up REST server and attach handlers."""



    rs = RestServer(debug=True)
    rs.add_route(TestHandler.ROUTE, TestHandler)
    rs.startup(address="localhost", port=port)

    def client() -> RestClient:
        return RestClient(f"http://localhost:{port}", retries=0)

    try:
        yield client
    finally:
        await rs.stop()
