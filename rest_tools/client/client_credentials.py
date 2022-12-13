# fmt:off
import logging
import time
from typing import Any

import requests

from .openid_client import OpenIDRestClient


class ClientCredentialsAuth(OpenIDRestClient):
    """A REST client that can handle token refresh using OpenID .well-known
    auto-discovery.

    Args:
        address (str): base address of REST API
        token_url (str): base address of token service
        client_id (str): client id
        client_secret (str): client secret
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
        client_secret: str,
        **kwargs: Any
    ) -> None:
        super().__init__(address=address, token_url=token_url, client_id=client_id, client_secret=client_secret, **kwargs)
        self.logger = logging.getLogger('ClientCredentialsAuth')

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

        if self.client_secret:
            # try making a new token
            args = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }

            try:
                r = requests.post(self.auth.token_url, data=args)
                r.raise_for_status()
                req = r.json()
            except Exception:
                self.refresh_token = None
            else:
                self.logger.debug('OpenID token created')
                self.access_token = req['access_token']
                self.refresh_token = None
                if self.access_token and self.update_func:
                    self.update_func(self.access_token, self.refresh_token)
                return

        raise Exception('No token available')
