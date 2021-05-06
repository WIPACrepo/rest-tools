"""Example client code.

Add some fruit to the server, then read them back.
"""

import asyncio
import logging
import sys
from typing import Any, Dict

from wipac_telemetry import tracing_tools

sys.path.append("../..")
from rest_tools.client import RestClient  # noqa: E402 # pylint: disable=C0413,E0401
from rest_tools.server import Auth  # noqa: E402 # pylint: disable=C0413,E0401


async def main() -> None:
    """Establish REST connection, make some requests, handle responses."""
    admin_token = Auth("secret").create_token("foo", payload={"role": "admin"})
    user_token = Auth("secret").create_token("foo", payload={"role": "user"})

    rc = RestClient("http://localhost:8080/api", token=admin_token)
    rc_user = RestClient("http://localhost:8080/api", token=user_token)

    @tracing_tools.spanned()
    async def _request_post_1() -> None:
        await rc.request("POST", "/fruits", {"name": "apple"})

    @tracing_tools.spanned()
    async def _request_post_2() -> None:
        await rc.request("POST", "/fruits", {"name": "banana"})

    await _request_post_1()
    await _request_post_2()

    @tracing_tools.spanned()
    async def _request_get() -> Dict[str, Any]:
        return await rc_user.request("GET", "/fruits")  # type: ignore[no-any-return]

    ret = await _request_get()
    assert ret["fruits"] == {"apple": {"name": "apple"}, "banana": {"name": "banana"}}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
