"""Tools for working with OpenAPI."""

import logging
import os
from pathlib import Path
from typing import Any, cast

import requests
import tornado

# 'openapi' imports
try:
    import openapi_core
    from jsonschema_path import SchemaPath
    from openapi_spec_validator import validate
    from openapi_spec_validator.readers import read_from_filename
    from openapi_core.contrib import requests as openapi_core_requests
    from openapi_core.exceptions import OpenAPIError

    openapi_available = True
except (ImportError, ModuleNotFoundError) as e:
    # if client code wants to use these features, then let the built-in errors raise
    openapi_available = False


LOGGER = logging.getLogger(__name__)


########################################################################################
# OpenAPI spec manipulation
########################################################################################


def get_openapi_spec(fpath: Path) -> tuple["openapi_core.OpenAPI", dict[str, Any]]:
    """Get the OpenAPI spec and its dict representation."""
    spec_dict, base_uri = read_from_filename(str(fpath))

    # first, validate the spec
    LOGGER.info(f"validating OpenAPI spec for {base_uri} ({fpath})")
    validate(spec_dict)  # no exception -> spec is valid

    # next, create the OpenAPI object
    _path = SchemaPath.from_file_path(str(fpath))
    _spec = openapi_core.OpenAPI(_path)

    return (
        _spec,
        cast(dict[str, Any], spec_dict),
    )


def get_version_vmaj(openapi_spec: "openapi_core.OpenAPI") -> str:
    """Get the major version of the OpenAPI spec, like 'v0', 'v1', etc."""
    return "v" + openapi_spec.version.major


########################################################################################
# Server-side endpoint request validation
########################################################################################


def validate_request(openapi_spec: "OpenAPI"):  # type: ignore
    """A REST-endpoint wrapper to validate requests against an OpenAPI spec.

    Example:
    ```
    class MyRestHandler(RestHandler):

        @validate_request(config.OPENAPI_SPEC)
        async def get(self) -> None: ...
    ```
    """
    if not openapi_available:
        raise RuntimeError(
            "openapi cannot be imported! perhaps you meant to pip install it?"
        )

    def make_wrapper(method):  # type: ignore[no-untyped-def]
        async def wrapper(zelf: tornado.web.RequestHandler, *args, **kwargs):  # type: ignore[no-untyped-def]
            LOGGER.debug("validating with openapi spec")
            # NOTE - don't change data (unmarshal) b/c we are downstream of data separation
            try:
                # https://openapi-core.readthedocs.io/en/latest/validation.html
                openapi_spec.validate_request(
                    _http_server_request_to_openapi_request(zelf.request),
                )
            except ValidationError as e:  # type: ignore
                LOGGER.error(f"invalid request: {e.__class__.__name__} - {e}")
                if isinstance(  # look at the ORIGINAL exception that caused this error
                    e.__context__,
                    openapi_core.validation.schemas.exceptions.InvalidSchemaValue,  # type: ignore
                ):
                    reason = "; ".join(  # to client
                        # verbose details after newline
                        str(x).split("\n", maxsplit=1)[0]
                        for x in e.__context__.schema_errors
                    )
                else:
                    reason = str(e)  # to client
                if os.getenv("CI"):
                    # in prod, don't fill up logs w/ traces from invalid data
                    LOGGER.exception(e)
                raise tornado.web.HTTPError(
                    status_code=400,
                    log_message=f"{e.__class__.__name__}: {e}",  # to stderr
                    reason=reason,  # to client
                )
            except Exception as e:
                LOGGER.error(f"unexpected exception: {e.__class__.__name__} - {e}")
                LOGGER.exception(e)
                raise tornado.web.HTTPError(
                    status_code=400,
                    log_message=f"{e.__class__.__name__}: {e}",  # to stderr
                    reason=None,  # to client (don't send possibly sensitive info)
                )

            return await method(zelf, *args, **kwargs)

        return wrapper

    return make_wrapper


def _http_server_request_to_openapi_request(
    req: tornado.httputil.HTTPServerRequest,
) -> "openapi_core_requests.RequestsOpenAPIRequest":
    """Convert a `tornado.httputil.HTTPServerRequest` to openapi's type."""
    if not openapi_available:
        raise RuntimeError(
            "openapi cannot be imported! perhaps you meant to pip install it?"
        )
    return openapi_core_requests.RequestsOpenAPIRequest(  # type: ignore
        requests.Request(
            method=req.method.lower() if req.method else "get",
            url=f"{req.protocol}://{req.host}{req.uri}",
            headers=req.headers,
            files=req.files,
            data=req.body if not req.body_arguments else None,  # see below
            params=req.query_arguments,
            # auth=None,
            cookies=req.cookies,
            # hooks=None,
            json=req.body_arguments if req.body_arguments else None,  # see above
        )
    )


########################################################################################################################
# Client-side
########################################################################################################################


async def request_and_validate(
    rc: "RestClient",
    openapi_spec: "openapi_core.OpenAPI",
    method: str,
    path: str,
    args: dict[str, Any] | None = None,
) -> Any:
    """Make request and validate the response against an OpenAPI spec.

    Useful for testing and debugging.

    NOTE: this essentially mimics RestClient.request() with added features.
    """
    url, kwargs = rc._prepare(method, path, args=args)

    # run request as async in case of other dependent, concurrent actions (ex: test suite runs server in same process)
    response = await asyncio.wrap_future(rc.session.request(method, url, **kwargs))  # type: ignore[var-annotated,arg-type]

    try:
        openapi_spec.validate_response(
            openapi_core_requests.RequestsOpenAPIRequest(response.request),
            openapi_core_requests.RequestsOpenAPIResponse(response),  # type: ignore[arg-type] # openapi uses protocols
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
