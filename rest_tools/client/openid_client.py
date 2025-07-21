"""A simple REST json client using `requests`_ for the http connection.

.. _requests: http://docs.python-requests.org

The REST protocol is built on http(s), with the body containing
a json-encoded dictionary as necessary.
"""

import logging
from typing import Any, Callable, Optional, Union

import jwt
import requests
from requests.auth import HTTPBasicAuth

from .client import RestClient
from ..utils.auth import OpenIDAuth


# fmt:off


class OpenIDRestClient(RestClient):
    """A REST client that can handle token refresh using OpenID .well-known
    auto-discovery.

    Args:
        address (str): base address of REST API
        token_url (str): base address of token service
        client_id (str): client id
        client_secret (str): client secret (optional - required to generate new refresh token)
        refresh_token (str): initial refresh token (optional)
        update_func (callable): a function that gets called when the access and refresh tokens are updated (optional)
        timeout (int): request timeout (optional)
        retries (int): number of retries to attempt (optional)
    """

    def __init__(
        self,
        address: str,
        token_url: str,
        refresh_token: Union[str, bytes],
        client_id: str,
        client_secret: Optional[str] = None,
        update_func: Optional[
            Callable[[Union[str, bytes], Optional[Union[str, bytes]]], None]
        ] = None,
        **kwargs: Any,
    ) -> None:
        self.auth = OpenIDAuth(token_url)
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.update_func = update_func

        super().__init__(
            address,
            logger=kwargs.pop('logger', logging.getLogger('OpenIDRestClient')),
            token=self._openid_token,
            **kwargs,
        )

        # initial call to verify things work
        self._openid_token()

    def _get_scopes(self) -> str:
        try:
            return jwt.decode(self.refresh_token, options={'verify_signature': False}).get('scope', '')
        except jwt.exceptions.DecodeError:
            # in case the token is opaque
            return ''

    def _openid_token(self) -> str:
        if not self.auth.token_url:
            self.auth._refresh_keys()

        # try the refresh token
        scopes = self._get_scopes()
        self.logger.debug('refreshing the token. scopes: %s', scopes)
        args = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'scope': scopes,
        }
        kwargs = {}
        if self.client_secret:
            kwargs['auth'] = HTTPBasicAuth(self.client_id, self.client_secret)

        try:
            r = requests.post(self.auth.token_url, data=args, **kwargs)  # type: ignore[arg-type]
            r.raise_for_status()
            req = r.json()
        except requests.exceptions.HTTPError as exc:
            self.logger.debug('%r', exc.response.text)
            try:
                req = exc.response.json()
            except Exception:
                req = {}
            error = req.get('error', '')
            raise Exception(f'Token request failed: {error}') from exc
        else:
            self.logger.debug('OpenID token refreshed')
            access_token = req['access_token']
            if 'refresh_token' in req:
                self.refresh_token = req['refresh_token']
                if access_token and self.update_func:
                    self.update_func(access_token, self.refresh_token)
            return access_token


class RegisterOpenIDClient:
    def __init__(self, address: str, client_name: str, scopes: Union[list[str], None] = None):
        self.address = address
        self.client_name = client_name
        self.scopes = scopes if scopes else []
        self._registration_path = None
        self._registration_token = None

    async def register_client(self):
        rc = RestClient(self.address, retries=0)
        meta = {
            'grant_types': [
                'authorization_code',
                'urn:ietf:params:oauth:grant-type:device_code',
            ],
            'client_name': self.client_name,
            'scope': ' '.join(self.scopes),
        }
        ret = await rc.request('POST', '/client', meta)
        self._registration_path = ret['registration_client_uri'][len(self.address):]
        self._registration_token = ret['registration_access_token']

        client_id = ret['client_id']
        client_secret = ret['client_secret']
        return (client_id, client_secret)

    async def delete_client(self, *args, **kwargs):
        if self._registration_path and self._registration_token:
            rc2 = RestClient(self.address, token=self._registration_token, retries=0)
            await rc2.request('DELETE', self._registration_path)

    __aenter__ = register_client
    __aexit__ = delete_client
