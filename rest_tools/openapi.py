"""Tools for working with OpenAPI."""

from logging import Logger
from pathlib import Path
from typing import Any, cast

# 'openapi' imports
try:
    import openapi_core
    from jsonschema_path import SchemaPath
    from openapi_spec_validator import validate
    from openapi_spec_validator.readers import read_from_filename

    openapi_available = True
except (ImportError, ModuleNotFoundError) as e:
    # if client code wants to use these features, then let the built-in errors raise
    openapi_available = False


def get_openapi_spec(
    fpath: Path,
    logger: Logger,
) -> tuple["openapi_core.OpenAPI", dict[str, Any]]:
    """Get the OpenAPI spec and its dict representation."""
    spec_dict, base_uri = read_from_filename(str(fpath))

    # first, validate the spec
    logger.info(f"validating OpenAPI spec for {base_uri} ({fpath})")
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
