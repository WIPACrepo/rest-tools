import base64
import logging
import urllib.parse
from typing import Any
from unittest.mock import Mock

import jwt
import jwt.algorithms
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from requests import PreparedRequest

from rest_tools.client import OpenIDRestClient
from rest_tools.utils.auth import Auth

from rest_tools.utils.json_util import json_encode  # isort:skip # noqa # pylint: disable=C0413


@pytest.fixture
def well_known_mock(requests_mock: Mock):
    result = {
        'token_endpoint': 'http://test/token',
        'jwks_uri': 'http://test/jwks',
    }

    def response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        return json_encode(result).encode("utf-8")
    requests_mock.get("http://test/.well-known/openid-configuration", content=response)


def to_base64url(n):
    """Converts an integer to a Base64URL-encoded string without padding."""
    # Convert integer to bytes (big-endian)
    byte_length = (n.bit_length() + 7) // 8
    der_bytes = n.to_bytes(byte_length, byteorder='big')
    # Encode and remove padding '='
    return base64.urlsafe_b64encode(der_bytes).decode('utf-8').rstrip('=')


@pytest.fixture
def make_auth(well_known_mock, requests_mock: Mock):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Build the JWK
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    jwk['kid'] = 'test-key'
    jwk['alg'] = 'RS256'
    jwks = {"keys": [jwk]}

    def jwks_response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        return json_encode(jwks).encode("utf-8")
    requests_mock.get('http://test/jwks', content=jwks_response)

    # auth for making tokens
    auth = Auth(secret=priv_pem, algorithm='RS256')

    yield auth


def test_scopes(make_auth, requests_mock: Mock) -> None:
    """Test that we can get scopes from the refresh token"""
    initial_refresh_token = make_auth.create_token('xxx', payload={'scope':'foo'}, headers={'kid': 'test-key'})

    def token_response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode({
            "access_token": make_auth.create_token('sub', headers={'kid': 'test-key'}),
            "refresh_token": make_auth.create_token('xxx', payload={'scope':'foo'}, headers={'kid': 'test-key'}),
        }).encode("utf-8")
    requests_mock.post('http://test/token', content=token_response)

    rc = OpenIDRestClient('http://test-api', 'http://test', refresh_token=initial_refresh_token, client_id='client-id')
    s = rc._get_scopes()
    assert s == 'foo'


def test_scopes_opaque_token(make_auth, requests_mock: Mock) -> None:
    """Test that we fail over gracefully for opaque tokens that are not jwt"""
    initial_refresh_token = 'my_opaque_token'

    def token_response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode({
            "access_token": make_auth.create_token('sub', headers={'kid': 'test-key'}),
            "refresh_token": 'my_opaque_token',
        }).encode("utf-8")
    requests_mock.post('http://test/token', content=token_response)

    rc = OpenIDRestClient('http://test-api', 'http://test', refresh_token=initial_refresh_token, client_id='client-id')

    s = rc._get_scopes()
    assert s == ''


def test_scopes_invalid_alg(make_auth, requests_mock: Mock) -> None:
    """Test that we get an exception if we get a bad jwt"""
    bad_auth = Auth('secret'*20)
    initial_refresh_token = bad_auth.create_token('xxx', payload={'scope':'foo'}, headers={'kid': 'test-key'})

    # fails initially because of the call to _get_scopes in the __init__
    with pytest.raises(jwt.exceptions.InvalidAlgorithmError):
        OpenIDRestClient('http://test-api', 'http://test', refresh_token=initial_refresh_token, client_id='client-id')


def test_scopes_jwt_key_not_found(make_auth, requests_mock: Mock) -> None:
    """Test that we fail over gracefully for private keys"""
    other_auth = Auth('secret'*20)
    initial_refresh_token = other_auth.create_token('sub', payload={'scope':'foo'}, headers={'kid': 'priv-key'})

    def token_response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode({
            "access_token": make_auth.create_token('sub', headers={'kid': 'test-key'}),
            "refresh_token": other_auth.create_token('sub', payload={'scope':'foo'}, headers={'kid': 'priv-key'}),
        }).encode("utf-8")
    requests_mock.post('http://test/token', content=token_response)

    rc = OpenIDRestClient('http://test-api', 'http://test', refresh_token=initial_refresh_token, client_id='client-id')

    s = rc._get_scopes()
    assert s == 'foo'


@pytest.fixture
def make_auth_okp(well_known_mock, requests_mock: Mock):
    private_key = ed25519.Ed25519PrivateKey.generate()
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Build the JWK
    jwk = jwt.algorithms.OKPAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    jwk['kid'] = 'test-key'
    jwk['alg'] = 'EdDSA'
    jwks = {"keys": [jwk]}

    def jwks_response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        return json_encode(jwks).encode("utf-8")
    requests_mock.get('http://test/jwks', content=jwks_response)

    # auth for making tokens
    auth = Auth(secret=priv_pem, algorithm='EdDSA')

    yield auth


def test_scopes_other_alg(make_auth_okp, requests_mock: Mock) -> None:
    """Test that we can get scopes from the refresh token"""
    initial_refresh_token = make_auth_okp.create_token(
        'xxx',
        payload={'scope':'foo'},
        headers={'kid': 'test-key'},
    )

    def token_response(req: PreparedRequest, ctx: Any) -> bytes:  # pylint: disable=W0613
        assert req.body is not None
        body = urllib.parse.parse_qs(str(req.body))
        logging.debug('token request args: %r', body)
        assert body['client_id'][0] == 'client-id'
        return json_encode({
            "access_token": make_auth_okp.create_token('sub', headers={'kid': 'test-key'}),
            "refresh_token": make_auth_okp.create_token('xxx', payload={'scope':'foo'}, headers={'kid': 'test-key'}),
        }).encode("utf-8")
    requests_mock.post('http://test/token', content=token_response)

    with pytest.raises(jwt.exceptions.InvalidAlgorithmError):
        OpenIDRestClient('http://test-api', 'http://test', refresh_token=initial_refresh_token, client_id='client-id')
        
    OpenIDRestClient('http://test-api', 'http://test', refresh_token=initial_refresh_token, client_id='client-id', algorithms=['EdDSA'])

    rc = OpenIDRestClient('http://test-api', 'http://test', refresh_token=initial_refresh_token, client_id='client-id', algorithm='EdDSA')
    s = rc._get_scopes()
    assert s == 'foo'
