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

    # duck typing magic
    class _DuckResponse(openapi_core.protocols.Response):
        """AKA 'openapi_core_requests.RequestsOpenAPIResponse' but correct."""

        @property
        def data(self) -> Optional[bytes]:
            return response.content

        @property
        def status_code(self) -> int:
            return int(response.status_code)

        @property
        def content_type(self) -> str:
            # application/json; charset=UTF-8  ->  application/json
            # ex: openapi_core.validation.response.exceptions.DataValidationError: DataValidationError: Content for the following mimetype not found: application/json; charset=UTF-8. Valid mimetypes: ['application/json']
            return str(response.headers.get("Content-Type", "")).split(";")[0]
            # alternatively, look at how 'openapi_core_requests.RequestsOpenAPIRequest.mimetype' handles similarly

        @property
        def headers(self) -> dict:
            return dict(response.headers)

    openapi_spec.validate_response(
        openapi_core_requests.RequestsOpenAPIRequest(response.request),
        _DuckResponse(),
    )

    out = rc._decode(response.content)
    response.raise_for_status()
    return out


########################################################################################################################
