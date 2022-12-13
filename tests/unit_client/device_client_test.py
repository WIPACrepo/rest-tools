import logging
from unittest.mock import Mock
import urllib.parse

import pytest
from requests import PreparedRequest

from rest_tools.client import DeviceGrantAuth  # isort:skip # noqa # pylint: disable=C0413
from rest_tools.utils.json_util import json_encode  # isort:skip # noqa # pylint: disable=C0413


@pytest.fixture
def well_known_mock(requests_mock: Mock):
    result = {
        'token_endpoint': 'http://test/token',
        'device_authorization_endpoint': 'http://test/device',
    }

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        return json_encode(result).encode("utf-8")
    requests_mock.get("http://test/.well-known/openid-configuration", content=response)


def test_10_success(well_known_mock, requests_mock: Mock) -> None:
    device_result = {
        'device_code': 'XXXXXXXXXXXXXXXXXXXXXXXX',
        'user_code': 'XXXX-XXXX',
        'verification_uri': 'http://test/device_verification',
        'expires_in': 600,
        'interval': 0.1,
    }

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('device request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode(device_result).encode("utf-8")
    requests_mock.post('http://test/device', content=response)

    token_result = {
        'access_token': 'XXXXXXXXXXXXX',
        'refresh_token': 'YYYYYYYYYYYYY',
        'token_type': 'bearer',
    }

    def response2(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        if body['grant_type'][0] != 'refresh_token':
            assert body['grant_type'][0] == 'urn:ietf:params:oauth:grant-type:device_code'
            assert body['device_code'][0] == device_result['device_code']
        return json_encode(token_result).encode("utf-8")
    requests_mock.post('http://test/token', content=response2)

    DeviceGrantAuth('http://test-api', 'http://test', 'client-id')


def test_20_device_unsupported(requests_mock: Mock) -> None:
    result = {
        'token_endpoint': 'http://test/token',
    }

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        return json_encode(result).encode("utf-8")
    requests_mock.get("http://test/.well-known/openid-configuration", content=response)

    with pytest.raises(RuntimeError, match='not supported'):
        DeviceGrantAuth('http://test-api', 'http://test', 'client-id')


def test_21_device_bad_client(well_known_mock, requests_mock: Mock) -> None:
    device_result = {
        'error': 'invalid_client'
    }

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('device request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        ctx.status_code = 401
        return json_encode(device_result).encode("utf-8")
    requests_mock.post('http://test/device', content=response)

    with pytest.raises(RuntimeError, match='invalid_client'):
        DeviceGrantAuth('http://test-api', 'http://test', 'client-id')


def test_22_device_code_timeout(well_known_mock, requests_mock: Mock) -> None:
    device_result = {
        'device_code': 'XXXXXXXXXXXXXXXXXXXXXXXX',
        'user_code': 'XXXX-XXXX',
        'verification_uri': 'http://test/device_verification',
        'expires_in': 600,
        'interval': 0.1,
    }

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('device request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode(device_result).encode("utf-8")
    requests_mock.post('http://test/device', content=response)

    token_result = {
        'error': 'expired_token'
    }

    def response2(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        if body['grant_type'][0] != 'refresh_token':
            assert body['grant_type'][0] == 'urn:ietf:params:oauth:grant-type:device_code'
            assert body['device_code'][0] == device_result['device_code']
        ctx.status_code = 400
        return json_encode(token_result).encode("utf-8")
    requests_mock.post('http://test/token', content=response2)

    with pytest.raises(RuntimeError, match='expired_token'):
        DeviceGrantAuth('http://test-api', 'http://test', 'client-id')


def test_23_device_code_denied(well_known_mock, requests_mock: Mock) -> None:
    device_result = {
        'device_code': 'XXXXXXXXXXXXXXXXXXXXXXXX',
        'user_code': 'XXXX-XXXX',
        'verification_uri': 'http://test/device_verification',
        'expires_in': 600,
        'interval': 0.1,
    }

    def response(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('device request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode(device_result).encode("utf-8")
    requests_mock.post('http://test/device', content=response)

    token_result = {
        'error': 'access_denied'
    }

    def response2(req: PreparedRequest, ctx: object) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        if body['grant_type'][0] != 'refresh_token':
            assert body['grant_type'][0] == 'urn:ietf:params:oauth:grant-type:device_code'
            assert body['device_code'][0] == device_result['device_code']
        ctx.status_code = 400
        return json_encode(token_result).encode("utf-8")
    requests_mock.post('http://test/token', content=response2)

    with pytest.raises(RuntimeError, match='access_denied'):
        DeviceGrantAuth('http://test-api', 'http://test', 'client-id')
