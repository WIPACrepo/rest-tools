"""Test script for auth."""

# fmt:off
# pylint: skip-file

import time

import jwt
import pytest

# local imports
from rest_tools.utils import auth

from .fixtures import (  # noqa: F401 # gen_keys_bytes uses gen_keys
    gen_keys,
    gen_keys_bytes,
)


def test_auth_create_token():
    a = auth.Auth('secret')
    now = time.time()
    tok = a.create_token('subj', expiration=20, payload={'type':'foo'})

    data = jwt.decode(tok, 'secret', algorithms=['HS512'])
    assert data['sub'] == 'subj'
    assert data['type'] == 'foo'
    assert data['exp'] < now+21


def test_auth_validate():
    a = auth.Auth('secret')
    tok = a.create_token('subj', expiration=20)
    data = a.validate(tok)
    assert data['sub'] == 'subj'


def test_auth_validate_leeway():
    a = auth.Auth('secret', leeway=0)
    tok = a.create_token('subj', expiration=-1)
    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        a.validate(tok)

    a = auth.Auth('secret', leeway=10)
    tok = a.create_token('subj', expiration=-1)
    data = a.validate(tok)
    assert data['sub'] == 'subj'


def test_auth_validate_exp_int():
    a = auth.Auth('secret', integer_times=False)
    tok = a.create_token('subj', expiration=125)
    data = a.validate(tok)
    assert isinstance(data['exp'], float)

    a = auth.Auth('secret', integer_times=True)
    tok = a.create_token('subj', expiration=125)
    data = a.validate(tok)
    assert isinstance(data['exp'], int)


def test_auth_validate_aud():
    a = auth.Auth('secret', audience=['bar'])
    tok = a.create_token('subj', expiration=20, payload={'aud': 'foo'})
    with pytest.raises(jwt.exceptions.InvalidAudienceError):
        a.validate(tok)

    a.validate(tok, audience='foo')


def test_auth_validate_aud_none():
    a = auth.Auth('secret', audience=None)
    tok = a.create_token('subj', expiration=20)
    a.validate(tok)


def test_auth_validate_iss():
    a = auth.Auth('secret', issuer='foo')
    tok = a.create_token('subj', expiration=20)
    data = a.validate(tok)
    assert data['iss'] == 'foo'

    with pytest.raises(jwt.exceptions.InvalidIssuerError):
        a._validate(tok, 'secret', issuers=['bar'])


def test_auth_validate_iss_none():
    a = auth.Auth('secret', issuer='foo')
    tok = a.create_token('subj', expiration=20)
    data = a._validate(tok, 'secret')
    assert data['iss'] == 'foo'


def test_auth_rsa(gen_keys_bytes):  # noqa: F811
    a = auth.Auth(gen_keys_bytes[0], pub_secret=gen_keys_bytes[1], algorithm='RS256')
    tok = a.create_token('subj', expiration=20)
    data = jwt.decode(tok, gen_keys_bytes[1], algorithms=['RS256'])
    assert data['sub'] == 'subj'

    data = a.validate(tok)
    assert data['sub'] == 'subj'


def test_auth_rsa_aud_iss(gen_keys_bytes):  # noqa: F811
    a = auth.Auth(gen_keys_bytes[0], pub_secret=gen_keys_bytes[1], issuer='foo', audience=['bar'], issuers=['foo'], algorithm='RS256')
    tok = a.create_token('subj', expiration=20, payload={'aud': 'bar'})
    a.validate(tok)
