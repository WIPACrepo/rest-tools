"""Test client.utils.request_and_validate module."""

import re
from typing import AsyncIterator, Callable

import openapi_core
import pytest
import pytest_asyncio
import requests
import tornado
from jsonschema_path import SchemaPath
from openapi_core.templating.paths.exceptions import PathNotFound
from openapi_core.templating.responses.exceptions import ResponseNotFound
from openapi_core.validation.response.exceptions import DataValidationError

from rest_tools.client import RestClient
from rest_tools.client.utils import request_and_validate
from rest_tools.server import RestHandler, RestServer


@pytest_asyncio.fixture
async def server(port: int) -> AsyncIterator[Callable[[], RestClient]]:
    """Start up REST server and attach handlers."""
    rs = RestServer(debug=True)

    class TestHandler(RestHandler):
        ROUTE = "/echo/this"

        async def post(self) -> None:
            if self.get_argument("raise", None):
                raise tornado.web.HTTPError(self.get_argument("raise"), "it's an error")
            self.write({"resp-echo": self.get_argument("echo", {})})

    rs.add_route(TestHandler.ROUTE, TestHandler)
    rs.startup(address="localhost", port=port)

    def client() -> RestClient:
        return RestClient(f"http://localhost:{port}", retries=0)

    try:
        yield client
    finally:
        await rs.stop()


OPENAPI_SPEC = openapi_core.OpenAPI(
    SchemaPath.from_dict(
        {
            "openapi": "3.1.0",
            "info": {
                "title": "Test Schema",
                "summary": "A schema for testing",
                "description": "This is a test description",
                "contact": {
                    "name": "WIPAC Developers",
                    "url": "icecube.wisc.edu",
                    "email": "developers@icecube.wisc.edu",
                },
                "license": {"name": "MIT License"},
                "version": "0.0.0",
            },
            "components": {
                "parameters": {},
                "schemas": {
                    "EchoObject": {
                        "type": "object",
                        "properties": {
                            "foo": {"type": "integer"},
                        },
                        "required": ["foo"],
                        "additionalProperties": False,
                    },
                },
            },
            "paths": {
                "/echo/this": {
                    # "parameters": [],
                    "post": {
                        # "requestBody": {},  # NOTE: these tests don't include input validation, so don't bother
                        "responses": {
                            "200": {
                                "description": "echoing this value",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "resp-echo": {
                                                    "$ref": "#/components/schemas/EchoObject"
                                                },
                                            },
                                        }
                                    }
                                },
                            },
                            "400": {
                                "description": "invalid request arguments",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "code": {
                                                    "description": "http error code",
                                                    "type": "integer",
                                                },
                                                "error": {
                                                    "description": "http error reason",
                                                    "type": "string",
                                                },
                                            },
                                            "required": ["code", "error"],
                                            "additionalProperties": False,
                                        }
                                    }
                                },
                            },
                        },
                    },
                },
            },
        }
    )
)


async def test_000__valid(server: Callable[[], RestClient]) -> None:
    """Test valid request data."""
    rc = server()

    # validate response data
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "POST", "/echo/this", {"echo": {"foo": 123}}
    )
    assert res == {"resp-echo": {"foo": 123}}

    # validate response error
    with pytest.raises(requests.HTTPError) as e:
        await request_and_validate(
            rc,
            OPENAPI_SPEC,
            "POST",
            "/echo/this",
            {"raise": 400},
        )
    assert e.value.response.status_code == 400


async def test_010__invalid(server: Callable[[], RestClient]) -> None:
    """Test invalid request data."""
    rc = server()

    with pytest.raises(
        PathNotFound, match=re.escape(f"Path not found for {rc.address}/foo/bar/baz")
    ):
        await request_and_validate(rc, OPENAPI_SPEC, "GET", "/foo/bar/baz")

    # validate response data

    with pytest.raises(
        DataValidationError,
        match=re.escape(
            "InvalidData: Value {'resp-echo': 123} not valid for schema of type object: (<ValidationError: \"123 is not of type 'object'\">,)"
        ),
    ):
        await request_and_validate(
            rc, OPENAPI_SPEC, "POST", "/echo/this", {"echo": 123}
        )

    with pytest.raises(
        DataValidationError,
        match=re.escape(
            "InvalidData: Value {'resp-echo': {'foo': 'hello'}} not valid for schema of type object: (<ValidationError: \"'hello' is not of type 'integer'\">,)"
        ),
    ):
        await request_and_validate(
            rc, OPENAPI_SPEC, "POST", "/echo/this", {"echo": {"foo": "hello"}}
        )

    with pytest.raises(
        DataValidationError,
        match=re.escape(
            "Value {'resp-echo': {}} not valid for schema of type object: (<ValidationError: \"'foo' is a required property\">,)"
        ),
    ):
        await request_and_validate(rc, OPENAPI_SPEC, "POST", "/echo/this", {"baz": 123})

    # validate response error
    with pytest.raises(
        ResponseNotFound, match=re.escape("Unknown response http status: 401")
    ):
        await request_and_validate(
            rc,
            OPENAPI_SPEC,
            "POST",
            "/echo/this",
            {"raise": 401},
        )
