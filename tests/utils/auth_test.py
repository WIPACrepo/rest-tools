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

    tok = jwt.encode({'sub':'subj','exp':now-1}, 'secret', algorithm='HS512')
    with pytest.raises(Exception):
        a.validate(tok)


def test_auth_rsa(gen_keys_bytes):  # noqa: F811
    a = auth.Auth(gen_keys_bytes[0], pub_secret=gen_keys_bytes[1], algorithm='RS256')
    tok = a.create_token('subj', expiration=20, type='foo')
    data = jwt.decode(tok, gen_keys_bytes[1], algorithms=['RS256'])
    assert data['sub'] == 'subj'

    data = a.validate(tok)
    assert data['sub'] == 'subj'
