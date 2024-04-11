"""Test client.utils.request_and_validate module."""

import asyncio
from typing import AsyncIterator

import openapi_core
import pytest
import requests
import tornado
from jsonschema_path import SchemaPath
from openapi_core.validation.response import exceptions
from tornado.web import RequestHandler

from rest_tools.client import RestClient
from rest_tools.client.utils import request_and_validate
from rest_tools.server import RestServer


@pytest.fixture(scope="session")  # persist for entire test suite
async def rc() -> AsyncIterator[RestClient]:
    """Start up REST server and attach handlers."""

    class TestHandler(RequestHandler):
        ROUTE = "/echo/this"

        def post(self) -> None:
            if self.get_argument("raise", None):
                raise tornado.web.HTTPError(400, self.get_argument("raise"))
            self.write(self.get_argument("echo"))

    rs = RestServer(debug=True)
    rs.add_route(TestHandler.ROUTE, TestHandler, {})
    rs.startup(address="localhost", port=8080)
    server_task = asyncio.create_task(asyncio.Event().wait())
    await asyncio.sleep(0)

    yield RestClient("https://localhost", retries=0)

    server_task.cancel()


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
                                            "$ref": "#/components/schemas/EchoObject"
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


def test_000__valid(rc: RestClient) -> None:
    """Test valid request data."""

    # validate response data
    res = request_and_validate(
        rc, OPENAPI_SPEC, "POST", "/echo/this", {"echo": {"foo": 123}}
    )
    assert res == {"foo": 123}

    # validate response error
    with pytest.raises(requests.HTTPError) as e:
        request_and_validate(
            rc,
            OPENAPI_SPEC,
            "POST",
            "/echo/this",
            {"raise": {"code": 123, "error": "its an error"}},
        )
    assert e.value.response.status_code == 400


def test_010__invalid(rc: RestClient) -> None:
    """Test invalid request data."""

    # validate response data

    with pytest.raises(exceptions.DataValidationError):
        request_and_validate(rc, OPENAPI_SPEC, "POST", "/echo/this", {"echo": 123})

    with pytest.raises(exceptions.DataValidationError):
        request_and_validate(
            rc, OPENAPI_SPEC, "POST", "/echo/this", {"echo": {"foo": "string"}}
        )

    with pytest.raises(exceptions.DataValidationError):
        request_and_validate(rc, OPENAPI_SPEC, "POST", "/echo/this", {"baz": 123})

    # validate response error
    with pytest.raises(exceptions.DataValidationError):
        request_and_validate(
            rc,
            OPENAPI_SPEC,
            "POST",
            "/echo/this",
            {"raise": {"foo": 123, "bar": "its an error"}},
        )
