"""Test route handlers for the OpenAPI spec validation."""

import openapi_core
from jsonschema_path import SchemaPath

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
