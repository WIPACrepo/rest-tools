import base64
import logging
import urllib.parse
from typing import Any
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
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
    public_numbers = private_key.public_key().public_numbers()

    # Build the JWK manually using n and e
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key",         # Key ID for rotation/lookup
                "use": "sig",              # Key usage (signing)
                "alg": "RS256",            # Algorithm
                "n": to_base64url(public_numbers.n), # Modulus as hex
                "e": to_base64url(public_numbers.e), # Exponent as hex
            }
        ]
    }

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
