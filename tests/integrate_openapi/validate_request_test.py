"""Test route handlers for the OpenAPI spec validation."""

from typing import AsyncIterator, Callable

import openapi_core
import pytest_asyncio
from jsonschema_path import SchemaPath

from rest_tools.client import RestClient
from rest_tools.client.utils import request_and_validate
from rest_tools.server import RestServer, RestHandler, validate_request


@pytest_asyncio.fixture
async def server(port: int) -> AsyncIterator[Callable[[], RestClient]]:
    """Start up REST server and attach handlers."""
    rs = RestServer(debug=True)

    class FooNoArgsHandler(RestHandler):
        ROUTE = "/foo/no-args"

        @validate_request(OPENAPI_SPEC)
        async def get(self) -> None:
            self.write({"message": "hello world"})

        @validate_request(OPENAPI_SPEC)
        async def post(self) -> None:
            self.write({"message": "hello world"})

    class FooURLParamsHandler(RestHandler):
        ROUTE = r"/foo/params/(?P<the_id>\w+)/(?P<the_name>\w+)$"

        @validate_request(OPENAPI_SPEC)
        async def get(self, the_id: str, the_name: str) -> None:
            self.write({"message": f"got {the_id} {the_name}"})

        @validate_request(OPENAPI_SPEC)
        async def post(self, the_id: str, the_name: str) -> None:
            self.write({"message": f"posted {the_id} {the_name}"})

    class FooArgsHandler(RestHandler):
        ROUTE = "/foo/args"

        @validate_request(OPENAPI_SPEC)
        async def get(self) -> None:
            # args embedded in url's query string
            self.write({"message": f"hello {self.get_argument('name')}"})

        @validate_request(OPENAPI_SPEC)
        async def post(self) -> None:
            # args in JSON
            self.write({"message": f"hey {self.get_argument('nickname')}"})

    class FooURLParamsAndArgsHandler(RestHandler):
        ROUTE = r"/foo/params-and-args/(?P<the_id>\w+)/(?P<the_name>\w+)$"

        @validate_request(OPENAPI_SPEC)
        async def get(self, the_id: str, the_name: str) -> None:
            # args embedded in url's query
            self.write(
                {"message": f"got {the_id} {the_name} -- {self.get_argument('why')}"}
            )

        @validate_request(OPENAPI_SPEC)
        async def post(self, the_id: str, the_name: str) -> None:
            # args in JSON
            self.write(
                {"message": f"posted {the_id} {the_name} -- {self.get_argument('why')}"}
            )

    rs.add_route(FooNoArgsHandler.ROUTE, FooNoArgsHandler)
    rs.add_route(FooURLParamsHandler.ROUTE, FooURLParamsHandler)
    rs.add_route(FooArgsHandler.ROUTE, FooArgsHandler)
    rs.add_route(FooURLParamsAndArgsHandler.ROUTE, FooURLParamsAndArgsHandler)
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
                "parameters": {
                    "TaskforceUUIDParam": {
                        "name": "taskforce_uuid",
                        "in": "path",
                        "required": True,
                        "description": "the taskforce object's uuid",
                        "schema": {"type": "string"},
                    },
                },
                "schemas": {
                    "TaskDirectiveObject": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "cluster_locations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                            },
                            "task_image": {"type": "string"},
                            "task_args": {"type": "string"},
                            "timestamp": {"type": "integer"},
                            "aborted": {"type": "boolean"},
                        },
                        "required": [],
                        "additionalProperties": False,
                    },
                },
            },
            "paths": {
                "/echo/this": {
                    "parameters": [],
                    "get": {
                        "responses": {
                            "200": {
                                "description": "the openapi schema",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {},
                                            "additionalProperties": True,
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
                        }
                    },
                },
                "/task/directive": {
                    "parameters": [],
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "cluster_locations": {
                                                "$ref": "#/components/schemas/TaskDirectiveObject/properties/cluster_locations"
                                            },
                                            "task_image": {
                                                "$ref": "#/components/schemas/TaskDirectiveObject/properties/task_image"
                                            },
                                            "task_args": {
                                                "$ref": "#/components/schemas/TaskDirectiveObject/properties/task_args"
                                            },
                                            "n_workers": {
                                                "$ref": "#/components/schemas/TaskforceObject/properties/n_workers"
                                            },
                                            "worker_config": {
                                                "$ref": "#/components/schemas/TaskforceObject/properties/worker_config"
                                            },
                                            "environment": {
                                                "$ref": "#/components/schemas/TaskforceObject/properties/container_config/properties/environment"
                                            },
                                            "input_files": {
                                                "$ref": "#/components/schemas/TaskforceObject/properties/container_config/properties/input_files"
                                            },
                                        },
                                        "required": [
                                            "cluster_locations",
                                            "task_image",
                                            "task_args",
                                            "worker_config",
                                        ],
                                        "additionalProperties": False,
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "the matching task directive",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/TaskDirectiveObject"
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
    """Test server handler methods with valid data."""
    rc = server()

    # no args allowed
    res = await request_and_validate(rc, OPENAPI_SPEC, "GET", "/foo/no-args")
    assert res == {"message": "hello world"}
    res = await request_and_validate(rc, OPENAPI_SPEC, "POST", "/foo/no-args")
    assert res == {"message": "hello world"}

    # url params
    res = await request_and_validate(rc, OPENAPI_SPEC, "GET", "/foo/params/123/hank")
    assert res == {"message": f"got 123 hank"}
    res = await request_and_validate(rc, OPENAPI_SPEC, "POST", "/foo/params/456/tilly")
    assert res == {"message": f"got 456 tilly"}

    # args
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "GET", "/foo/args", {"name": "tim"}
    )
    assert res == {"message": f"hello tim"}
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "POST", "/foo/args", {"nickname": "timbo"}
    )
    assert res == {"message": f"hey timbo"}

    # args + url params
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "GET", "/foo/params/789/book", {"why": "the future"}
    )
    assert res == {"message": f"got 789 book -- the future"}
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "POST", "/foo/params/248/saru", {"why": "the past"}
    )
    assert res == {"message": f"posted 248 saru -- the past"}


async def test_010__invalid(server: Callable[[], RestClient]) -> None:
    """Test server handler methods with invalid data."""
