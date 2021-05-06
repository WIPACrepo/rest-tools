"""Example server code.

Make a fruit API.
"""

import asyncio
import logging
import sys
from typing import Any, Dict

from wipac_telemetry import tracing_tools  # noqa: E402 # pylint: disable=C0413,E0401

sys.path.append("../..")
from rest_tools.server import (
    RestHandler,
    RestHandlerSetup,
    RestServer,
    role_authorization,
)
from rest_tools.utils.json_util import json_decode


class FruitsHanlder(RestHandler):
    """Handle Fruit requests."""

    def initialize(self, fruit: Dict[str, Any], *args: Any, **kwargs: Any) -> None:
        """Initialize."""
        super().initialize(*args, **kwargs)
        self.fruit = fruit  # pylint: disable=W0201

    @tracing_tools.spanned(from_client=True)
    @role_authorization(roles=["admin", "user"])
    async def get(self) -> None:
        """Write existing fruits."""
        assert tracing_tools.get_current_span().parent.span_id

        logging.info("fruits: %r", self.fruit)

        self.write({"fruits": self.fruit})

    @tracing_tools.spanned(from_client=True)
    @role_authorization(roles=["admin"])
    async def post(self) -> None:
        """Handle a new fruit."""
        assert tracing_tools.get_current_span().parent.span_id

        body = json_decode(self.request.body)
        logging.info("body: %r", body)

        self.fruit[body["name"]] = body

        self.write({})


def main() -> None:
    """Establish and run REST server."""
    logging.basicConfig(level=logging.DEBUG)

    args = RestHandlerSetup({"auth": {"secret": "secret"}, "debug": True})
    args["fruit"] = {}  # this could be a DB, but a dict works for now

    server = RestServer(debug=True)
    server.add_route("/api/fruits", FruitsHanlder, args)
    server.startup(address="localhost", port=8080)

    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
