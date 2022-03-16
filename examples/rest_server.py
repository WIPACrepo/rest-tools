"""Example server code.

Make a fruit API.
"""

import asyncio
import logging
from typing import Any, Dict

from rest_tools.server import (  # noqa: E402 # pylint: disable=C0413,E0401
    RestHandler,
    RestHandlerSetup,
    RestServer,
    role_authorization,
)
from rest_tools.utils.json_util import (  # noqa: E402 # pylint: disable=C0413,E0401
    json_decode,
)
from wipac_telemetry import tracing_tools  # type: ignore[import]


class FruitsHanlder(RestHandler):
    """Handle Fruit requests."""

    def initialize(self, fruit: Dict[str, Any], *args: Any, **kwargs: Any) -> None:  # type: ignore
        """Initialize."""
        super().initialize(*args, **kwargs)
        self.fruit = fruit  # pylint: disable=W0201

    @role_authorization(roles=["admin", "user"])
    async def get(self) -> None:
        """Write existing fruits."""
        assert tracing_tools.get_current_span().parent.span_id  # type: ignore[attr-defined]

        logging.info("fruits: %r", self.fruit)

        self.write({"fruits": self.fruit})

    @role_authorization(roles=["admin"])
    async def post(self) -> None:
        """Handle a new fruit."""
        assert tracing_tools.get_current_span().parent.span_id  # type: ignore[attr-defined]

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
