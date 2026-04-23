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
    from jsonschema_path.typing import Schema

    from .client import RestClient


LOGGER = logging.getLogger(__name__)

sdict = dict[str, Any]

########################################################################################
# OpenAPI spec manipulation
########################################################################################


def load_openapi_spec(
    fpath: Path,
    metadata_from_package: str,
) -> tuple["openapi_core.OpenAPI", sdict]:
    """
    Loads and validates an OpenAPI specification file while optionally incorporating
    project metadata.

    Parameters:
        fpath: Path
            The file path to the OpenAPI specification.
        metadata_from_package: str
            The name of the package to use for metadata to add to the spec.

    Returns:
        A tuple containing:
            - the schema as an OpenAPI object
            - the schema as a dictionary
    """
    _schema, base_uri = read_from_filename(str(fpath))
    if metadata_from_package:
        _schema = _populate_spec_info_from_pkg_metadata(_schema, metadata_from_package)

    # validate the spec
    LOGGER.info(f"validating OpenAPI spec for {base_uri} ({fpath})")
    validate(_schema)  # no exception -> spec is valid

    # create the OpenAPI object
    _spec = openapi_core.OpenAPI(SchemaPath.from_dict(_schema, base_uri=base_uri))

    return _spec, cast(sdict, dict(_schema))


def _populate_spec_info_from_pkg_metadata(spec: "Schema", dist_name: str) -> "Schema":
    """Populate the 'info' section of an OpenAPI spec with project metadata, for package dist_name."""
    if sys.version_info < (3, 12):
        # python <= 3.11 does not support PackageMetadata.get()
        # -- our server apps will need to run on python 3.12+, which most already do
        raise RuntimeError(
            "openapi_tools._populate_spec_info_from_installed_metadata() requires python 3.12+"
        )

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

    new_info: dict[str, str | Any] = {
        # NOTE: do not add/override 'title' or 'version'
        # - 'title' and 'version' are required by the OpenAPI spec
        # - auto-populating 'version' from the project would not allow testing new
        #       major versions -- think: crossing over from v1 to v2, endpoints may change
        "summary": md.get("Summary", ""),
        "description": md.get("Description", ""),
        "contact": {
            "name": md.get("Maintainer", md.get("Author", "")),
            "email": md.get("Maintainer-email", md.get("Author-email", "")),
            "url": _first_project_url(md),
        },
        "license": {
            "name": md.get("License-Expression", md.get("License", "")),
        },
    }

    # check overrides
    for k in new_info:
        if spec["info"].get(k):
            raise RuntimeError(
                f"Cannot auto-populate OpenAPI specification field 'info.{k}' -- it's already populated"
            )

    spec = dict(spec)  # cast in order to add key
    spec["info"] = {
        **spec.get("info", {}),
        **new_info,  # override/add
    }
    return spec


def get_version_vmaj(openapi_dict: sdict) -> str:
    """Get the major version of the OpenAPI spec (info.version); like 'v0', 'v1', etc."""
    return "v" + openapi_dict["info"]["version"].split(".")[0]


########################################################################################
# Server-side endpoint request validation
########################################################################################


def _schema_error_to_human_readable(err):  # noqa: C901  # ignore "too complex"
    """Format a jsonschema ValidationError as 'path: reason'.

    The offending value (err.instance) is intentionally NOT included in the
    returned string: request bodies can contain secrets (tokens, auth URLs,
    env-var values) or be very large (full event payloads), and a 400
    response body is not the right place to reflect either back to the
    client. The full value remains available server-side via LOGGER.error
    for debugging.
    """
    field_path = ".".join(str(p) for p in err.absolute_path)

    # Reconstruct the reason without including err.instance (the bad value).
    # err.validator is the failing keyword ('type', 'pattern', 'required',
    # 'oneOf', ...); err.validator_value is its schema value.
    keyword, constraint = err.validator, err.validator_value

    if keyword in ("required", "additionalProperties"):
        # og: "'docker_tag' is a required property"
        # og: "Additional properties are not allowed ('scan_id' was unexpected)"
        return str(err).split("\n", 1)[0]
    elif keyword == "type":
        # og: "'' is not of type 'integer'"
        _type_alias = {
            # communicate python equivalents for the more abstract JSON types
            "boolean": " (bool)",
            "array": " (list)",
            "object": " (dict)",
            "null": " (None)",
        }
        reason = f"must be type {constraint!r}{_type_alias.get(constraint, '')}"
    elif keyword == "pattern":
        # og: "' ' does not match '\\S'"
        reason = f"must match the pattern {constraint!r}"
    elif keyword == "minLength":
        # og: "'' is too short"
        reason = f"must be at least {constraint} characters long"
    elif keyword == "maxLength":
        # og: "'aaaa...' is too long"
        reason = f"must be no more than {constraint} characters long"
    elif keyword == "minimum":
        # og: "0 is less than the minimum of 1"
        reason = f"must be at least {constraint}"
    elif keyword == "maximum":
        # og: "30 is greater than the maximum of 25"
        reason = f"must be no more than {constraint}"
    elif keyword == "enum":
        # og: "'fake' is not one of ['real', 'real_event', ...]"
        reason = f"must be one of: {', '.join(repr(v) for v in constraint)}"
    elif keyword in ("oneOf", "anyOf"):
        # og: "X is not valid under any of the given schemas"
        # NOTE: 'oneOf' vs 'anyOf'
        #   'anyOf' fires for both "matched 0 branches" and "matched multiple branches";
        #   jsonschema's default message distinguishes the two, but from the user's
        #   POV the fix is the same: send a value that fits exactly one form.
        #   So -- this makes both keywords ('oneOf' and 'anyOf') practically the same,
        #   using the following wording...
        reason = "must match one of the accepted types"
    elif keyword == "minItems":
        # og: "[] is too short"
        reason = f"must have at least {constraint} items"
    elif keyword == "maxItems":
        # og: "[...] is too long"
        reason = f"must have no more than {constraint} items"
    elif keyword == "minProperties":
        # og: "{} does not have enough properties"
        reason = f"must have at least {constraint} entries"
    elif keyword == "maxProperties":
        # og: "{...} has too many properties"
        reason = f"must have no more than {constraint} entries"
    elif keyword == "uniqueItems":
        # og: "[1, 1] has non-unique elements"
        reason = "items must be unique"
    else:
        # fall-through: future-proof new keywords
        reason = f"failed {keyword!r} constraint"

    return f"{field_path!r}: {reason}" if field_path else reason


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
                # get reason
                if isinstance(  # look at the ORIGINAL exception that caused this error
                    e.__context__,
                    openapi_core.validation.schemas.exceptions.InvalidSchemaValue,  # type: ignore
                ):
                    reason = "; ".join(
                        _schema_error_to_human_readable(x)
                        for x in e.__context__.schema_errors
                    )
                else:
                    reason = str(e)  # to client
                # send 400
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
    response = await asyncio.wrap_future(rc.session.request(method, url, **kwargs))  # type: ignore[var-annotated,arg-type]  # ty: ignore[invalid-argument-type]

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
