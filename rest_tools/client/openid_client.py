"""A simple REST json client using `requests`_ for the http connection.

.. _requests: http://docs.python-requests.org

The REST protocol is built on http(s), with the body containing
a json-encoded dictionary as necessary.
"""

# fmt:off
import logging
from typing import Any, Callable, Optional, Union

import requests

from ..utils.auth import OpenIDAuth
from .client import RestClient


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
        update_func: Optional[Callable[[Union[str, bytes], Optional[Union[str, bytes]]], None]] = None,
        **kwargs: Any
    ) -> None:
        self.auth = OpenIDAuth(token_url)
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.update_func = update_func

        super().__init__(address, logger=logging.getLogger('OpenIDRestClient'),
                         token=self._openid_token, **kwargs)

        # initial call to verify things work
        self._openid_token()

    def _openid_token(self) -> str:
        # try the refresh token
        args = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
        }
        if self.client_secret:
            args['client_secret'] = self.client_secret

        try:
            r = requests.post(self.auth.token_url, data=args)
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
