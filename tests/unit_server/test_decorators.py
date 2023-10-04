from unittest.mock import AsyncMock, MagicMock

import pytest
from tornado.web import HTTPError

from rest_tools.server import decorators


async def test_authenticated():
    mock = AsyncMock()
    f = decorators.authenticated(mock)

    self = MagicMock()
    self.current_user = None
    with pytest.raises(HTTPError, match='authentication failed'):
        await f(self)
    mock.assert_not_awaited()

    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub'}
    await f(self)
    mock.assert_awaited()

    await f(self, 1, a='b')
    mock.assert_called_with(self, 1, a='b')


async def test_catch_error():
    @decorators.catch_error
    async def test_passthrough(self):
        raise HTTPError(400, reason='foo')

    self = MagicMock()
    self.send_error = MagicMock()
    with pytest.raises(HTTPError, match='foo'):
        await test_passthrough(self)
    self.send_error.assert_not_called()

    @decorators.catch_error
    async def test_error(self):
        raise Exception('blah')

    await test_error(self)
    self.send_error.assert_called_with(500, reason='Error in MagicMock')


async def test_role_authorization():
    mock = AsyncMock()
    f = decorators.role_authorization(roles=['write'])(mock)

    self = MagicMock()
    self.current_user = None
    with pytest.raises(HTTPError, match='authentication failed'):
        await f(self)
    mock.assert_not_awaited()

    self = MagicMock()
    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub'}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub', 'role': 'read'}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.auth_data = {'sub': 'sub', 'role': 'write'}
    await f(self)
    mock.assert_awaited()

    await f(self, 1, a='b')
    mock.assert_called_with(self, 1, a='b')


async def test_scope_role_auth():
    mock = AsyncMock()
    f = decorators.scope_role_auth(roles=['write'], prefix='test')(mock)

    self = MagicMock()
    self.current_user = None
    with pytest.raises(HTTPError, match='authentication failed'):
        await f(self)
    mock.assert_not_awaited()

    self = MagicMock()
    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub'}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub', 'scope': 'test:read'}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub', 'scope': 'test:read foo:write write'}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.auth_data = {'sub': 'sub', 'scope': 'test:read foo:write test:write'}
    await f(self)
    mock.assert_awaited()

    await f(self, 1, a='b')
    mock.assert_called_with(self, 1, a='b')


async def test_keycloak_role_auth():
    mock = AsyncMock()
    f = decorators.keycloak_role_auth(roles=['write'], prefix='my.roles')(mock)

    self = MagicMock()
    self.current_user = None
    with pytest.raises(HTTPError, match='authentication failed'):
        await f(self)
    mock.assert_not_awaited()

    self = MagicMock()
    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub'}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub', 'my': {'roles': ['read']}}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.auth_data = {'sub': 'sub', 'my': {'roles': ['write']}}
    await f(self)
    mock.assert_awaited()

    await f(self, 1, a='b')
    mock.assert_called_with(self, 1, a='b')


async def test_token_attribute_role_mapping_auth():
    mock = AsyncMock()
    d = decorators.token_attribute_role_mapping_auth(
        role_attrs={'write': ['my.roles=write']},
    )
    f = d(roles=['write'])(mock)

    self = MagicMock()
    self.current_user = None
    with pytest.raises(HTTPError, match='authentication failed'):
        await f(self)
    mock.assert_not_awaited()

    self = MagicMock()
    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub'}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.current_user = 'sub'
    self.auth_data = {'sub': 'sub', 'my': {'roles': ['read']}}
    with pytest.raises(HTTPError, match='authorization failed'):
        await f(self)
    mock.assert_not_awaited()

    self.auth_data = {'sub': 'sub', 'my': {'roles': ['write']}}
    await f(self)
    mock.assert_awaited()

    await f(self, 1, a='b')
    mock.assert_called_with(self, 1, a='b')


async def test_token_attribute_role_mapping_auth_groups():
    mock = AsyncMock()
    d = decorators.token_attribute_role_mapping_auth(
        role_attrs={r'\1': ['my.roles=(write)', 'my.roles=(read)']},
        group_attrs={r'\1': [r'groups=(\w+)']},
    )
    f = d(roles=['write'])(mock)

    self = MagicMock()
    self.auth_data = {'sub': 'sub', 'my': {'roles': ['write']}, 'groups': ['foo', 'bar']}
    await f(self, 1, a='b')
    mock.assert_called_with(self, 1, a='b')
    assert self.auth_groups == ['bar', 'foo']  #: in sorted order
