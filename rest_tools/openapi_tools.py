"""Tools for working with OpenAPI."""

import asyncio
import importlib
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import requests
import tornado

# 'openapi' imports
try:
    import openapi_core
    from jsonschema_path import SchemaPath
    from jsonschema_path.typing import Schema
    from openapi_core.contrib import requests as openapi_core_requests
    from openapi_core.exceptions import OpenAPIError
    from openapi_core.validation.exceptions import ValidationError
    from openapi_spec_validator import validate
    from openapi_spec_validator.readers import read_from_filename

    openapi_available = True
except (ImportError, ModuleNotFoundError):
    # if client code wants to use these features, then let the built-in errors raise
    openapi_available = False

if TYPE_CHECKING:  # prevent circular imports at runtime
    from .client import RestClient


LOGGER = logging.getLogger(__name__)

sdict = dict[str, Any]

########################################################################################
# OpenAPI spec manipulation
########################################################################################


def load_openapi_spec(
    fpath: Path,
    add_project_metadata: bool,
) -> tuple["openapi_core.OpenAPI", sdict]:
    """Get the OpenAPI spec and its dict representation.

    If `add_project_metadata` is True, then the spec's 'info' field will be populated
    using the installed project's metadata.
    """
    _schema, base_uri = read_from_filename(str(fpath))
    _schema = cast(sdict, dict(_schema))
    if add_project_metadata:
        _schema = _populate_spec_info_from_installed_metadata(_schema)

    # validate the spec
    LOGGER.info(f"validating OpenAPI spec for {base_uri} ({fpath})")
    validate(_schema)  # no exception -> spec is valid

    # create the OpenAPI object
    _spec = openapi_core.OpenAPI(SchemaPath.from_dict(_schema, base_uri=base_uri))

    return _spec, _schema


def _populate_spec_info_from_installed_metadata(spec: sdict) -> sdict:
    """Populate spec['info'] from installed project metadata only."""
    if spec.get("info"):
        raise RuntimeError(
            "Cannot auto-populate OpenAPI field 'info' -- it's already populated"
        )

    if sys.version_info < (3, 12):
        # python <= 3.11 does not support PackageMetadata.get()
        # -- our server apps will need to run on python 3.12+, which most already do
        raise RuntimeError(
            "openapi_tools._populate_spec_info_from_installed_metadata() requires python 3.12+"
        )

    top_name = (__package__ or __name__).split(".")[0]
    dist_name = importlib.metadata.packages_distributions()[top_name][0]  # use first
    md = importlib.metadata.metadata(dist_name)

    def _first_project_url(md: importlib.metadata.PackageMetadata) -> str:
        """Return the first parsed Project-URL value."""
        return next(
            (
                parts[1].strip()
                for item in md.get_all("Project-URL", [])
                if len(parts := item.split(",", 1)) == 2 and parts[1].strip()
            ),
            "",
        )

    info: dict[str, str | Any] = {
        "title": md.get("Name", ""),
        "summary": md.get("Summary", ""),
        "description": md.get("Description", ""),
        "version": md.get("Version", ""),
        "contact": {
            "name": md.get("Maintainer", md.get("Author", "")),
            "email": md.get("Maintainer-email", md.get("Author-email", "")),
            "url": _first_project_url(md),
        },
        "license": {
            "name": md.get("License-Expression", md.get("License", "")),
        },
    }

    spec = dict(spec)  # cast in order to add key
    spec["info"] = info
    return spec


def get_version_vmaj(openapi_spec: "openapi_core.OpenAPI") -> str:
    """Get the major version of the OpenAPI spec, like 'v0', 'v1', etc."""
    return "v" + openapi_spec.version.major


########################################################################################
# Server-side endpoint request validation
########################################################################################


def validate_request(openapi_spec: "openapi_core.OpenAPI"):  # type: ignore
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
