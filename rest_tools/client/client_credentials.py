# fmt:off
import logging
from typing import Any

import requests

from .client import RestClient
from ..utils.auth import OpenIDAuth


class ClientCredentialsAuth(RestClient):
    """A REST client that can handle token refresh using OpenID .well-known
    auto-discovery.

    Args:
        address (str): base address of REST API
        token_url (str): base address of token service
        client_id (str): client id
        client_secret (str): client secret
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
        self.auth = OpenIDAuth(token_url)
        self.client_id = client_id
        self.client_secret = client_secret
        super().__init__(address=address, token=self._make_token, logger=logging.getLogger('ClientCredentialsAuth'),
                         **kwargs)

    def _make_token(self) -> str:
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
        except requests.exceptions.HTTPError as exc:
            self.logger.debug('%r', exc.response.text)
            try:
                req = exc.response.json()
            except Exception:
                req = {}
            error = req.get('error', '')
            raise Exception(f'Token request failed: {error}') from exc
        else:
            self.logger.debug('OpenID token created')
            return req['access_token']
