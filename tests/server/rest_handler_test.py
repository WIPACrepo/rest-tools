import pytest
import json
import logging

from unittest.mock import MagicMock

from rest_tools.server import *
from rest_tools.server.stats import RouteStats
from rest_tools.utils.auth import Auth, OpenIDAuth
import jwt.algorithms
from tornado.web import Application, HTTPError

from ..util import *


def test_rest_handler_setup(requests_mock):
    ret = RestHandlerSetup({})
    assert ret['auth'] is None

    ret = RestHandlerSetup({'debug': True})
    assert ret['debug']

    ret = RestHandlerSetup({'auth': {'url': 'foo'}})
    assert ret['auth_url'] == 'foo'

    ret = RestHandlerSetup({'auth': {'secret': 'foo'}})
    assert isinstance(ret['auth'], Auth)

    requests_mock.get('http://foo/.well-known/openid-configuration', text=json.dumps({'token_endpoint': 'bar'}))
    ret = RestHandlerSetup({'auth': {'openid_url': 'http://foo'}})
    assert isinstance(ret['auth'], OpenIDAuth)
    assert requests_mock.called
    assert ret['auth_url'] == 'bar'

    ret = RestHandlerSetup({'rest_api': {'auth_key': 'foo'}})
    assert ret['module_auth_key'] == 'foo'

def test_rest_handler_initialize():
    rh = RestHandler()
    rh.initialize(debug=True)
    assert rh.debug

def test_rest_handler_get_current_user():
    a = Auth('secret')
    rh = RestHandler()
    rh.initialize(auth=a)
    rh.request = MagicMock()

    rh.request.headers = {}
    assert rh.get_current_user() is None

    token = a.create_token('subject', payload={'foo': 'bar'})
    rh.request.headers = {'Authorization': f'bearer {token}'}
    assert rh.get_current_user() == 'subject'
    assert rh.auth_data['foo'] == 'bar'
    assert rh.auth_key == token

def test_rest_handler_get_json_body_argument():
    rh = RestHandler()
    rh.initialize()
    rh.request = MagicMock()
    rh.request.body = json.dumps({'foo': 'bar'})

    assert rh.get_json_body_argument('foo') == 'bar'

    with pytest.raises(Exception):
        rh.get_json_body_argument('baz')

def test_rest_handler_get_argument():
    rh = RestHandler()
    rh.initialize()
    rh.request = MagicMock()
    rh.request.body = json.dumps({'foo': 'bar'})

    assert rh.get_argument('foo') == 'bar'

    with pytest.raises(Exception):
        rh.get_argument('baz')

def test_openid_login_handler_initialize(requests_mock):
    handler = OpenIDLoginHandler()
    with pytest.raises(RuntimeError):
        handler.initialize('foo', 'bar')

    requests_mock.get('http://foo/.well-known/openid-configuration', text=json.dumps({
        'authorization_endpoint': 'http://foo/auth',
        'token_endpoint': 'http://foo/token',
        'end_session_endpoint': 'http://foo/logout',
        'userinfo_endpoint': 'http://foo/userinfo',
    }))
    ret = RestHandlerSetup({'auth': {'openid_url': 'http://foo'}})
    handler.initialize('foo', 'bar', **ret)

    assert handler._OAUTH_AUTHORIZE_URL == 'http://foo/auth'
    assert handler._OAUTH_ACCESS_TOKEN_URL == 'http://foo/token'
    assert handler._OAUTH_LOGOUT_URL == 'http://foo/logout'
    assert handler._OAUTH_USERINFO_URL == 'http://foo/userinfo'

@pytest.mark.asyncio
async def test_openid_login_handler_get_authenticated_user(gen_keys, gen_keys_bytes, requests_mock):
    handler = OpenIDLoginHandler()

    auth = Auth(gen_keys_bytes[0], pub_secret=gen_keys_bytes[1], algorithm='RS256')

    requests_mock.get('http://foo/.well-known/openid-configuration', text=json.dumps({
        'authorization_endpoint': 'http://foo/auth',
        'token_endpoint': 'http://foo/token',
        'end_session_endpoint': 'http://foo/logout',
        'userinfo_endpoint': 'http://foo/userinfo',
        'jwks_uri': 'http://foo/jwks',
    }))
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(gen_keys[1]))
    jwk['kid'] = '123'
    logging.debug(jwk)
    requests_mock.get('http://foo/jwks', text=json.dumps({
        'keys': [jwk],
    }))
    ret = RestHandlerSetup({'auth': {'openid_url': 'http://foo'}})
    handler.initialize('foo', 'bar', **ret)

    token = auth.create_token('sub', headers={'kid': '123'})

    user_info = {
        'id_token': '{"id": "foo"}',
        'access_token': token,
        'expires_in': 3600,
    }
    async def fn(*args, **kwargs):
        ret = MagicMock()
        ret.body = json.dumps(user_info)
        return ret
    handler.get_auth_http_client = MagicMock()
    handler.get_auth_http_client.return_value.fetch = MagicMock(side_effect=fn)
    ret = await handler.get_authenticated_user('redirect', 'code')
    assert ret == user_info

def test_openid_login_handler_encode_decode_state(requests_mock):
    application = Application([], cookie_secret='secret')

    requests_mock.get('http://foo/.well-known/openid-configuration', text=json.dumps({
        'authorization_endpoint': 'http://foo/auth',
        'token_endpoint': 'http://foo/token',
        'end_session_endpoint': 'http://foo/logout',
        'userinfo_endpoint': 'http://foo/userinfo',
        'jwks_uri': 'http://foo/jwks',
    }))
    ret = RestHandlerSetup({'auth': {'openid_url': 'http://foo'}})
    ret['oauth_client_id'] = 'foo'
    ret['oauth_client_secret'] = 'bar'
    handler = OpenIDLoginHandler(application, MagicMock(), **ret)

    data = {'foo': 'bar'}
    state = handler._encode_state(data)
    data2 = handler._decode_state(state)
    assert data == data2

@pytest.mark.asyncio
async def test_openid_login_handler_get(gen_keys, gen_keys_bytes, requests_mock):
    application = Application([], cookie_secret='secret', login_url='/login', debug=True)

    auth = Auth(gen_keys_bytes[0], pub_secret=gen_keys_bytes[1], algorithm='RS256')

    requests_mock.get('http://foo/.well-known/openid-configuration', text=json.dumps({
        'authorization_endpoint': 'http://foo/auth',
        'token_endpoint': 'http://foo/token',
        'end_session_endpoint': 'http://foo/logout',
        'userinfo_endpoint': 'http://foo/userinfo',
        'jwks_uri': 'http://foo/jwks',
    }))
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(gen_keys[1]))
    jwk['kid'] = '123'
    logging.debug(jwk)
    requests_mock.get('http://foo/jwks', text=json.dumps({
        'keys': [jwk],
    }))
    ret = RestHandlerSetup({'auth': {'openid_url': 'http://foo'}})
    ret['oauth_client_id'] = 'foo'
    ret['oauth_client_secret'] = 'bar'

    request = MagicMock()
    handler = OpenIDLoginHandler(application, request, **ret)

    # first-time get
    handler.authorize_redirect = MagicMock()
    request.body = ''
    await handler.get()
    handler.authorize_redirect.assert_called()

    # get with code
    token = auth.create_token('sub', headers={'kid': '123'})
    user_info = {
        'id_token': '{"id": "foo"}',
        'access_token': token,
        'expires_in': 3600,
    }
    async def fn2(*args, **Kwargs):
        return user_info
    handler.get_authenticated_user = MagicMock(side_effect=fn2)

    request.body = '{"code": "thecode", "state": "state"}'
    handler._decode_state = MagicMock(return_value={})
    handler.write = MagicMock()
    await handler.get()
    handler.write.assert_called()
    assert handler.write.call_args[0][0] == user_info

    # get with error
    request.body = '{"error": true, "error_description": "the error"}'
    handler._decode_state = MagicMock(return_value={})
    handler.authorize_redirect = MagicMock()
    with pytest.raises(HTTPError, match='the error'):
        await handler.get()
    handler.authorize_redirect.assert_not_called()

