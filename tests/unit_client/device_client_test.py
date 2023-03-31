import logging
from typing import Any
from unittest.mock import Mock
import urllib.parse

import pytest
from requests import PreparedRequest

from rest_tools.client import DeviceGrantAuth, SavedDeviceGrantAuth
from rest_tools.client.device_client import _load_token_from_file, _save_token_to_file
from rest_tools.utils.json_util import json_encode  # isort:skip # noqa # pylint: disable=C0413


@pytest.fixture
def well_known_mock(requests_mock: Mock):
    result = {
        'token_endpoint': 'http://test/token',
        'device_authorization_endpoint': 'http://test/device',
    }

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
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

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
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

    def response2(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
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

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        return json_encode(result).encode("utf-8")
    requests_mock.get("http://test/.well-known/openid-configuration", content=response)

    with pytest.raises(RuntimeError, match='not supported'):
        DeviceGrantAuth('http://test-api', 'http://test', 'client-id')


def test_21_device_bad_client(well_known_mock, requests_mock: Mock) -> None:
    device_result = {
        'error': 'invalid_client'
    }

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
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

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('device request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode(device_result).encode("utf-8")
    requests_mock.post('http://test/device', content=response)

    token_result = {
        'error': 'expired_token'
    }

    def response2(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
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

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('device request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode(device_result).encode("utf-8")
    requests_mock.post('http://test/device', content=response)

    token_result = {
        'error': 'access_denied'
    }

    def response2(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
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


def test_100_saved_no_token(well_known_mock, requests_mock, tmp_path) -> None:
    device_result = {
        'device_code': 'XXXXXXXXXXXXXXXXXXXXXXXX',
        'user_code': 'XXXX-XXXX',
        'verification_uri': 'http://test/device_verification',
        'expires_in': 600,
        'interval': 0.1,
    }

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
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

    def response2(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        if body['grant_type'][0] != 'refresh_token':
            assert body['grant_type'][0] == 'urn:ietf:params:oauth:grant-type:device_code'
            assert body['device_code'][0] == device_result['device_code']
        return json_encode(token_result).encode("utf-8")
    requests_mock.post('http://test/token', content=response2)

    filepath = tmp_path / 'foo'
    SavedDeviceGrantAuth('http://test-api', 'http://test', filename=str(filepath), client_id='client-id')

    assert filepath.read_text() == token_result['refresh_token']


def test_101_load_save(tmp_path) -> None:
    filepath = tmp_path / 'foo'
    token = '12345'

    _save_token_to_file(filepath, token)
    assert token == _load_token_from_file(filepath)


def test_110_saved_good_token(well_known_mock, requests_mock, tmp_path) -> None:
    device_result = {
        'device_code': 'XXXXXXXXXXXXXXXXXXXXXXXX',
        'user_code': 'XXXX-XXXX',
        'verification_uri': 'http://test/device_verification',
        'expires_in': 600,
        'interval': 0.1,
    }

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        raise NotImplementedError()
    mock_device = requests_mock.post('http://test/device', content=response)

    token_result = {
        'access_token': 'XXXXXXXXXXXXX',
        'refresh_token': 'YYYYYYYYYYYYY',
        'token_type': 'bearer',
    }

    def response2(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        if body['grant_type'][0] != 'refresh_token':
            assert body['grant_type'][0] == 'urn:ietf:params:oauth:grant-type:device_code'
            assert body['device_code'][0] == device_result['device_code']
        return json_encode(token_result).encode("utf-8")
    mock_refresh = requests_mock.post('http://test/token', content=response2)

    filepath = tmp_path / 'foo'
    _save_token_to_file(filepath, 'badtoken')
    SavedDeviceGrantAuth('http://test-api', 'http://test', filename=str(filepath), client_id='client-id')

    assert filepath.read_text() == token_result['refresh_token']
    assert mock_device.call_count == 0
    assert mock_refresh.call_count == 1


def test_111_saved_expired_token(well_known_mock, requests_mock, tmp_path) -> None:
    device_result = {
        'device_code': 'XXXXXXXXXXXXXXXXXXXXXXXX',
        'user_code': 'XXXX-XXXX',
        'verification_uri': 'http://test/device_verification',
        'expires_in': 600,
        'interval': 0.1,
    }

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('device request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode(device_result).encode("utf-8")
    mock_device = requests_mock.post('http://test/device', content=response)

    token_result = {
        'access_token': 'XXXXXXXXXXXXX',
        'refresh_token': 'YYYYYYYYYYYYY',
        'token_type': 'bearer',
    }

    def response2(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        if body['grant_type'][0] == 'refresh_token':
            assert body['refresh_token'][0] != 'badtoken'
        else:
            assert body['grant_type'][0] == 'urn:ietf:params:oauth:grant-type:device_code'
            assert body['device_code'][0] == device_result['device_code']
        return json_encode(token_result).encode("utf-8")
    mock_refresh = requests_mock.post('http://test/token', content=response2)

    filepath = tmp_path / 'foo'
    _save_token_to_file(filepath, 'badtoken')
    SavedDeviceGrantAuth('http://test-api', 'http://test', filename=str(filepath), client_id='client-id')

    assert filepath.read_text() == token_result['refresh_token']
    assert mock_device.call_count == 1
    assert mock_refresh.call_count == 3
