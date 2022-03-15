"""Example client code.

Add some fruit to the server, then read them back.
"""

import asyncio
import logging

from rest_tools.client import RestClient  # noqa: E402 # pylint: disable=C0413,E0401
from rest_tools.utils import Auth  # noqa: E402 # pylint: disable=C0413,E0401
from wipac_telemetry import tracing_tools  # type: ignore[import]


@tracing_tools.spanned()
async def main() -> None:
    """Establish REST connection, make some requests, handle responses."""
    admin_token = Auth("secret").create_token("foo", payload={"role": "admin"})
    user_token = Auth("secret").create_token("foo", payload={"role": "user"})

    rc = RestClient("http://localhost:8080/api", token=admin_token)
    rc_user = RestClient("http://localhost:8080/api", token=user_token)

    # populate
    await rc.request("POST", "/fruits", {"name": "apple"})
    await rc.request("POST", "/fruits", {"name": "banana"})

    # # query
    ret = await rc_user.request("GET", "/fruits")
    assert ret["fruits"] == {"apple": {"name": "apple"}, "banana": {"name": "banana"}}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
