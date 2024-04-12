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
            self.write({"message": f"hey {self.get_argument('uf')}"})

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
            "info": {"title": "Foo API", "version": "1.0.0"},
            "components": {
                "parameters": {
                    "TheNameParam": {
                        "name": "the_name",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                },
                "schemas": {
                    "MessageResponseObject": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "additionalProperties": False,
                    },
                    "PseudonymsObject": {
                        "type": "object",
                        "properties": {
                            "alias": {"type": "string"},
                            "nickname": {"type": "string"},
                        },
                    },
                },
            },
            "paths": {
                "/foo/no-args": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Returns a hello world message",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {"type": "string"}
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "responses": {
                            "200": {
                                "description": "Returns a hello world message",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {"type": "string"}
                                            },
                                        }
                                    }
                                },
                            }
                        }
                    },
                },
                "/foo/params/{the_id}/{the_name}": {
                    "parameters": [
                        {
                            "name": "the_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {"$ref": "#/components/parameters/TheNameParam"},
                    ],
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Returns a message with the id and name",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MessageResponseObject"
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "responses": {
                            "200": {
                                "description": "Returns a message with the id and name",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MessageResponseObject"
                                        }
                                    }
                                },
                            }
                        }
                    },
                },
                "/foo/args": {
                    "get": {
                        "parameters": [
                            {
                                "name": "name",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Returns a hello message with the name",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MessageResponseObject"
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "nickname": {
                                                "$ref": "#/components/schemas/PseudonymsObject/properties/nickname"
                                            },
                                        },
                                        "required": ["nickname"],
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Returns a hey message with the nickname",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MessageResponseObject"
                                        }
                                    }
                                },
                            }
                        },
                    },
                },
                "/foo/params-and-args/{the_id}/{the_name}": {
                    "parameters": [
                        {
                            "name": "the_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {"$ref": "#/components/parameters/TheNameParam"},
                    ],
                    "get": {
                        "parameters": [
                            {
                                "name": "why",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Returns a message with the id, name and why",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MessageResponseObject"
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"why": {"type": "string"}},
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Returns a message with the id, name and why",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MessageResponseObject"
                                        }
                                    }
                                },
                            }
                        },
                    },
                },
            },
        },
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
    assert res == {"message": "got 123 hank"}
    res = await request_and_validate(rc, OPENAPI_SPEC, "POST", "/foo/params/456/tilly")
    assert res == {"message": "posted 456 tilly"}

    # args
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "GET", "/foo/args", {"name": "tim"}
    )
    assert res == {"message": "hello tim"}
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "POST", "/foo/args", {"nickname": "timbo"}
    )
    assert res == {"message": "hey timbo"}

    # args + url params
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "GET", "/foo/params-and-args/789/book", {"why": "the future"}
    )
    assert res == {"message": "got 789 book -- the future"}
    res = await request_and_validate(
        rc, OPENAPI_SPEC, "POST", "/foo/params-and-args/248/saru", {"why": "the past"}
    )
    assert res == {"message": "posted 248 saru -- the past"}


async def test_010__invalid(server: Callable[[], RestClient]) -> None:
    """Test server handler methods with invalid data."""

    # also add request to nonexistent path
