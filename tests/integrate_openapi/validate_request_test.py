"""Test route handlers for the OpenAPI spec validation."""

import re
from typing import AsyncIterator, Callable

import openapi_core
import pytest
import pytest_asyncio
import requests
from jsonschema_path import SchemaPath

from rest_tools.client import RestClient
from rest_tools.server import RestHandler, RestServer, validate_request


@pytest_asyncio.fixture
async def server(port: int) -> AsyncIterator[Callable[[], RestClient]]:
    """Start up REST server and attach handlers."""
    rs = RestServer(debug=True)

    class FooNoArgsHandler(RestHandler):
        ROUTE = "/foo/no-args"

        # NOTE: there is no way in openapi v3.1 to explicitly forbid extra query params
        # @validate_request(OPENAPI_SPEC)
        # async def get(self) -> None:
        #     self.write({"message": "hello world"})

        @validate_request(OPENAPI_SPEC)
        async def post(self) -> None:
            self.write({"message": "hello world"})

    class FooURLParamsHandler(RestHandler):
        ROUTE = r"/foo/params/(?P<the_id>\w+)/(?P<the_name>\w+)$"

        @validate_request(OPENAPI_SPEC)
        async def get(self, the_id: int, the_name: str) -> None:
            self.write({"message": f"got {the_id} {the_name}"})

        @validate_request(OPENAPI_SPEC)
        async def post(self, the_id: int, the_name: str) -> None:
            self.write({"message": f"posted {the_id} {the_name}"})

    class FooArgsHandler(RestHandler):
        ROUTE = "/foo/args"

        @validate_request(OPENAPI_SPEC)
        async def get(self) -> None:
            # args embedded in url's query string
            self.write({"message": f"hello {self.get_argument('rank')}"})

        @validate_request(OPENAPI_SPEC)
        async def post(self) -> None:
            # args in JSON
            self.write({"message": f"hey {self.get_argument('rank')}"})

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
                    "InfoObject": {
                        "type": "object",
                        "properties": {
                            "alias": {"type": "string"},
                            "rank": {"type": "integer"},
                        },
                    },
                },
            },
            "paths": {
                "/foo/no-args": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {  # no args allowed
                                        "type": "object",
                                        "properties": {},
                                        "required": [],
                                        "additionalProperties": False,
                                    }
                                }
                            }
                        },
                        # "responses": {},  # we're not validating/testing this, so don't bother
                    },
                },
                "/foo/params/{the_id}/{the_name}": {
                    "parameters": [
                        {
                            "name": "the_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                        {"$ref": "#/components/parameters/TheNameParam"},
                    ],
                    "get": {
                        # "responses": {},  # we're not validating/testing this, so don't bother
                    },
                    "post": {
                        # "responses": {},  # we're not validating/testing this, so don't bother
                    },
                },
                "/foo/args": {
                    "get": {
                        "parameters": [
                            {
                                "name": "rank",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        # "responses": {},  # we're not validating/testing this, so don't bother
                    },
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "rank": {
                                                "$ref": "#/components/schemas/InfoObject/properties/rank"
                                            },
                                        },
                                        "required": ["rank"],
                                        "additionalProperties": False,
                                    }
                                }
                            }
                        },
                        # "responses": {},  # we're not validating/testing this, so don't bother
                    },
                },
                "/foo/params-and-args/{the_id}/{the_name}": {
                    "parameters": [
                        {
                            "name": "the_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
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
                        # "responses": {},  # we're not validating/testing this, so don't bother
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
                        # "responses": {},  # we're not validating/testing this, so don't bother
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
    res = await rc.request("POST", "/foo/no-args")
    assert res == {"message": "hello world"}

    # url params
    res = await rc.request("GET", "/foo/params/123/hank")
    assert res == {"message": "got 123 hank"}
    res = await rc.request("POST", "/foo/params/456/tilly")
    assert res == {"message": "posted 456 tilly"}

    # args
    res = await rc.request("GET", "/foo/args", {"rank": 123})
    assert res == {"message": "hello 123"}
    res = await rc.request("POST", "/foo/args", {"rank": 456})
    assert res == {"message": "hey 456"}

    # args + url params
    res = await rc.request(
        "GET", "/foo/params-and-args/789/book", {"why": "the future"}
    )
    assert res == {"message": "got 789 book -- the future"}
    res = await rc.request("POST", "/foo/params-and-args/248/saru", {"why": "the past"})
    assert res == {"message": "posted 248 saru -- the past"}


async def test_010__invalid(server: Callable[[], RestClient]) -> None:
    """Test server handler methods with invalid data."""
    rc = server()

    #
    # no args allowed
    #

    # POST
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"Additional properties are not allowed ('have' was unexpected) for url: {rc.address}/foo/no-args"
        ),
    ) as e:
        # extra arg(s)
        await rc.request("POST", "/foo/no-args", {"have": "some args"})
    assert e.value.response.status_code == 400

    #
    # url params
    #

    # GET
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"Path parameter error: the_id for url: {rc.address}/foo/params/abc/888"
        ),
    ) as e:
        # bad type
        await rc.request("GET", "/foo/params/abc/888")
    assert e.value.response.status_code == 400

    # POST
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"Path parameter error: the_id for url: {rc.address}/foo/params/xyz/999"
        ),
    ) as e:
        # bad type
        await rc.request("POST", "/foo/params/xyz/999")
    assert e.value.response.status_code == 400

    #
    # args
    #

    # GET
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"Missing required query parameter: rank for url: {rc.address}/foo/args"
        ),
    ) as e:
        # missing arg(s)
        await rc.request("GET", "/foo/args")
    assert e.value.response.status_code == 400
    # with pytest.raises(requests.HTTPError) as e:
    #     # extra arg(s) -- NOTE: THESE ARE ACTUALLY OK
    #     await rc.request("GET", "/foo/args", {"name": "dwayne", "car": "vroom"})
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"Query parameter error: rank for url: {rc.address}/foo/args?rank=abc"
        ),
    ) as e:
        # bad type
        await rc.request("GET", "/foo/args", {"rank": "abc"})
    assert e.value.response.status_code == 400

    # POST
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"'rank' is a required property for url: {rc.address}/foo/args"
        ),
    ) as e:
        # missing arg(s)
        await rc.request("POST", "/foo/args")
    assert e.value.response.status_code == 400
    #
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"Additional properties are not allowed ('suv' was unexpected) for url: {rc.address}/foo/args"
        ),
    ) as e:
        # extra arg(s)
        await rc.request("POST", "/foo/args", {"rank": 123, "suv": "gas"})
    assert e.value.response.status_code == 400
    #
    with pytest.raises(
        requests.HTTPError,
        match=re.escape(
            f"400 Client Error: 'abc' is not of type 'integer' for url: {rc.address}/foo/args"
        ),
    ) as e:
        # bad type
        await rc.request("POST", "/foo/args", {"rank": "abc"})
    assert e.value.response.status_code == 400

    #
    # args + url params
    #

    # NOTE: not testing the compound cases, since that's exponentially more tests for
    #    little work. By now, we can safely assume that those cases are good since their
    #    components are *independent* (url params and args handling logics are independent)
