"""A simple REST json client using `requests`_ for the http connection.

.. _requests: http://docs.python-requests.org

The REST protocol is built on http(s), with the body containing
a json-encoded dictionary as necessary.
"""

# fmt:off
import logging
import time
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
        client_id: str,
        client_secret: Optional[str] = None,
        refresh_token: Optional[Union[str, bytes]] = None,
        update_func: Optional[Callable[[Union[str, bytes], Optional[Union[str, bytes]]], None]] = None,
        **kwargs: Any
    ) -> None:
        if (not client_secret) and (not refresh_token):
            raise RuntimeError('Either client_secret or refresh_token is required')

        super().__init__(address, **kwargs)
        self.logger = logging.getLogger('OpenIDRestClient')
        self.auth = OpenIDAuth(token_url)
        self.client_id = client_id
        self.client_secret = client_secret

        self.access_token = None
        self.refresh_token = refresh_token
        self.token_func = True  # type: ignore
        self.update_func = update_func
        self._get_token()

    def _get_token(self) -> None:
        if self.access_token:
            # check if expired
            try:
                data = self.auth.validate(self.access_token)
                if data['exp'] < time.time()-self._token_expire_delay_offset:
                    raise Exception()
                return
            except Exception:
                self.access_token = None
                self.logger.debug('OpenID token expired')

        if self.refresh_token:
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
            except Exception:
                self.refresh_token = None
            else:
                self.logger.debug('OpenID token refreshed')
                self.access_token = req['access_token']
                self.refresh_token = req['refresh_token'] if 'refresh_token' in req else None
                if self.access_token and self.update_func:
                    self.update_func(self.access_token, self.refresh_token)
                return

        raise Exception('No token available')
