"""Utility functions for RestClient."""

import asyncio
import logging
from typing import Any, Optional, Dict

from .client import RestClient

LOGGER = logging.getLogger(__name__)


########################################################################################################################


try:
    import openapi_core
    from openapi_core.contrib import requests as openapi_core_requests
    from openapi_core.exceptions import OpenAPIError
except ImportError:
    pass  # if client code wants to use these features, then let the built-in errors raise


async def request_and_validate(
    rc: RestClient,
    openapi_spec: "openapi_core.OpenAPI",
    method: str,
    path: str,
    args: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make request and validate the response against a given OpenAPI spec.

    Useful for testing and debugging.

    NOTE: this essentially mimics RestClient.request() with added features.
    """
    url, kwargs = rc._prepare(method, path, args=args)

    # run request as async in case of other dependent, concurrent actions (ex: test suite runs server in same process)
    response = await asyncio.wrap_future(rc.session.request(method, url, **kwargs))  # type: ignore[var-annotated,arg-type]

    try:
        openapi_spec.validate_response(
            openapi_core_requests.RequestsOpenAPIRequest(response.request),
            openapi_core_requests.RequestsOpenAPIResponse(response),
        )
    except OpenAPIError as e:
        LOGGER.error(
            f"OpenAPI response validator encountered an error: '{e}'; more info below."
        )
        LOGGER.info(f"request: {vars(response.request)}")
        LOGGER.info(f"response: {vars(response)}")
        raise

    out = rc._decode(response.content)
    response.raise_for_status()
    return out


########################################################################################################################
