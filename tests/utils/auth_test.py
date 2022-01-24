"""Test script for auth."""

# fmt:off
# pylint: skip-file

import time

import jwt
import pytest

# local imports
from rest_tools.utils import auth

from ..util import gen_keys, gen_keys_bytes  # noqa: F401 # gen_keys_bytes uses gen_keys


def test_auth_create_token():
    a = auth.Auth('secret')
    now = time.time()
    tok = a.create_token('subj', expiration=20, type='foo')

    data = jwt.decode(tok, 'secret', algorithms=['HS512'])
    assert data['sub'] == 'subj'
    assert data['type'] == 'foo'
    assert data['exp'] < now+21
    assert data['nbf'] > now-1


def test_auth_validate():
    a = auth.Auth('secret')
    now = time.time()
    tok = a.create_token('subj', expiration=20, type='foo')
    data = a.validate(tok)
    assert data['sub'] == 'subj'
    assert data['type'] == 'foo'

    tok = a.create_token('subj', expiration=-1, type='foo')
    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        a.validate(tok)

def test_auth_validate_aud():
    a = auth.Auth('secret', audience=['bar'])
    now = time.time()
    tok = a.create_token('subj', expiration=20, type='foo', payload={'aud': 'foo'})
    with pytest.raises(jwt.exceptions.InvalidAudienceError):
        a.validate(tok)

    a.validate(tok, audience='foo')

def test_auth_validate_aud_none():
    a = auth.Auth('secret', audience=None)
    now = time.time()
    tok = a.create_token('subj', expiration=20, type='foo')
    a.validate(tok)

def test_auth_validate_iss():
    a = auth.Auth('secret', issuer='foo')
    now = time.time()
    tok = a.create_token('subj', expiration=20, type='foo')
    data = a.validate(tok)
    assert data['iss'] == 'foo'

    with pytest.raises(jwt.exceptions.InvalidIssuerError):
        a._validate(tok, 'secret', issuers=['bar'])

def test_auth_validate_iss_none():
    a = auth.Auth('secret', issuer='foo')
    now = time.time()
    tok = a.create_token('subj', expiration=20, type='foo')
    data = a._validate(tok, 'secret')
    assert data['iss'] == 'foo'

def test_auth_rsa(gen_keys_bytes):  # noqa: F811
    a = auth.Auth(gen_keys_bytes[0], pub_secret=gen_keys_bytes[1], algorithm='RS256')
    tok = a.create_token('subj', expiration=20, type='foo')
    data = jwt.decode(tok, gen_keys_bytes[1], algorithms=['RS256'])
    assert data['sub'] == 'subj'

    data = a.validate(tok)
    assert data['sub'] == 'subj'

def test_auth_rsa_aud_iss(gen_keys_bytes):
    a = auth.Auth(gen_keys_bytes[0], pub_secret=gen_keys_bytes[1], issuer='foo', audience=['bar'], issuers=['foo'], algorithm='RS256')
    tok = a.create_token('subj', expiration=20, type='foo', payload={'aud': 'bar'})
    a.validate(tok)
