"""A simple REST json client using `requests`_ for the http connection.

.. _requests: http://docs.python-requests.org

The REST protocol is built on http(s), with the body containing
a json-encoded dictionary as necessary.
"""

# fmt:off

import asyncio
import logging
import os
import time
from typing import Any, Callable, Dict, Generator, Optional, Tuple, Union

import jwt
import requests
import wipac_telemetry.tracing_tools as wtt

from ..server import OpenIDAuth
from ..utils.json_util import JSONType, json_decode
from .session import AsyncSession, Session


def _to_str(s: Union[str, bytes]) -> str:
    if isinstance(s, bytes):
        return s.decode('utf-8')
    return s


class RestClient:
    """A REST client with token handling.

    Args:
        address (str): base address of REST API
        token (str): (optional) access token, or a function generating an access token
        timeout (int): (optional) request timeout (default: 60s)
        retries (int): (optional) number of retries to attempt (default: 10)
        username (str): (optional) auth-basic username
        password (str): (optional) auth-basic password
    """

    def __init__(
        self,
        address: str,
        token: Optional[Union[str, bytes, Callable[[], Union[str, bytes]]]] = None,
        timeout: float = 60.0,
        retries: int = 10,
        **kwargs: Any
    ) -> None:
        self.address = address
        self.timeout = timeout
        self.retries = retries
        self.kwargs = kwargs
        self.logger = logging.getLogger('RestClient')
        self.logger.setLevel('DEBUG')

        # token handling
        self.access_token: Optional[Union[str, bytes]] = None
        self.token_func: Optional[Callable[[], Union[str, bytes]]] = None
        if token:
            if isinstance(token, (str,bytes)):
                self.access_token = token
            elif callable(token):
                self.token_func = token

        self.session = self.open()  # start session

    def open(self, sync: bool = False) -> requests.Session:
        """Open the http session."""
        self.logger.debug('establish REST http session')
        if sync:
            self.session = Session(self.retries)
        else:
            self.session = AsyncSession(self.retries)
        self.session.headers = {  # type: ignore[assignment]
            'Content-Type': 'application/json',
        }
        if 'username' in self.kwargs and 'password' in self.kwargs:
            self.session.auth = (self.kwargs['username'], self.kwargs['password'])
        if 'sslcert' in self.kwargs:
            if 'sslkey' in self.kwargs:
                self.session.cert = (self.kwargs['sslcert'], self.kwargs['sslkey'])
            else:
                self.session.cert = self.kwargs['sslcert']
        if 'cacert' in self.kwargs:
            self.session.verify = self.kwargs['cacert']

        return self.session

    def close(self) -> None:
        """Close the http session."""
        self.logger.info('close REST http session')
        if self.session:
            self.session.close()

    def _get_token(self) -> None:
        if self.access_token:
            # check if expired
            try:
                # NOTE: PyJWT mis-type-hinted arg #1 as a str, but byte is also fine
                # https://github.com/jpadilla/pyjwt/pull/605#issuecomment-772082918
                data = jwt.decode(self.access_token, verify=False)  # type: ignore[arg-type]
                if data['exp'] < time.time()+5:
                    raise Exception()
                return
            except Exception:
                self.access_token = None
                self.logger.debug('token expired')

        try:
            self.access_token = self.token_func()  # type: ignore[misc]
        except Exception:
            self.logger.warning('acquiring access token failed')
            raise

    def _prepare(
        self,
        method: str,
        path: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Internal method for preparing requests."""
        if not args:
            args = {}

        # auto-inject the current span's info into the HTTP headers
        if wtt.get_current_span().is_recording():
            wtt.propagations.inject_span_carrier(self.session.headers)  # type: ignore[arg-type]

        if path.startswith('/'):
            path = path[1:]
        url = os.path.join(self.address, path)

        kwargs: Dict[str, Any] = {'timeout': self.timeout}

        if method in ('GET', 'HEAD'):
            # args should be urlencoded
            kwargs['params'] = args
        else:
            kwargs['json'] = args

        if self.token_func:
            self._get_token()

        if self.access_token:
            self.session.headers['Authorization'] = 'Bearer ' + _to_str(self.access_token)

        return (url, kwargs)

    def _decode(self, content: Union[str, bytes, bytearray]) -> JSONType:
        """Internal method for translating response from json."""
        if not content:
            self.logger.info('request returned empty string')
            return None
        try:
            return json_decode(content)
        except Exception:
            self.logger.info('json data: %r', content)
            raise

    @wtt.spanned(these=['method', 'path', 'self.address'], kind=wtt.SpanKind.CLIENT)
    async def request(
        self,
        method: str,
        path: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> JSONType:
        """Send request to REST Server.

        Async request - use with coroutines.

        Args:
            method (str): the http method
            path (str): the url path on the server
            args (dict): any arguments to pass

        Returns:
            dict: json dict or raw string
        """
        url, kwargs = self._prepare(method, path, args)
        try:
            # session: AsyncSession; So, self.session.request() -> Future
            r: requests.Response = await asyncio.wrap_future(self.session.request(method, url, **kwargs))  # type: ignore[arg-type]
            r.raise_for_status()
            return self._decode(r.content)
        except requests.exceptions.HTTPError as e:
            if method == 'DELETE' and e.response.status_code == 404:
                raise # skip the logging for an expected error
            self.logger.info('bad request: %s %s %r', method, path, args, exc_info=True)
            raise

    @wtt.spanned(these=['method', 'path', 'self.address'], kind=wtt.SpanKind.CLIENT)
    def request_seq(
        self,
        method: str,
        path: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> JSONType:
        """Send request to REST Server.

        Sequential version of `request`.

        Args:
            method (str): the http method
            path (str): the url path on the server
            args (dict): any arguments to pass

        Returns:
            dict: json dict or raw string
        """
        s = self.session
        try:
            self.open(sync=True)
            url, kwargs = self._prepare(method, path, args)
            r = self.session.request(method, url, **kwargs)
            r.raise_for_status()
            return self._decode(r.content)
        finally:
            self.session = s

    @wtt.spanned(these=['method', 'path', 'self.address'], kind=wtt.SpanKind.CLIENT)
    def request_stream(
        self,
        method: str,
        path: str,
        args: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = 8096,
    ) -> Generator[JSONType, None, None]:
        """Send request to REST Server, and stream results back.

        `chunk_size=None` will read data as it arrives
        in whatever size the chunks are received. `chunk_size`<`1`
        will be treated as `chunk_size=None`

        Args:
            method (str): the http method
            path (str): the url path on the server
            args (dict): any arguments to pass
            chunk_size (int): chunk size (see above)

        Returns:
            dict: json dict or raw string
        """
        if chunk_size is not None and chunk_size < 1:
            chunk_size = None

        s = self.session
        try:
            self.open(sync=True)
            url, kwargs = self._prepare(method, path, args)
            resp = self.session.request(method, url, stream=True, **kwargs)
            resp.raise_for_status()
            for line in resp.iter_lines(chunk_size=chunk_size, delimiter=b'\n'):
                decoded = self._decode(line.strip())
                if decoded:  # skip `None`
                    yield decoded
        finally:
            self.session = s


class OpenIDRestClient(RestClient):
    """A REST client that can handle token refresh using OpenID .well-known
    auto-discovery.

    Args:
        address (str): base address of REST API
        token_url (str): base address of token service
        refresh_token (str): initial refresh token
        client_id (str): client id
        client_secret (str): client secret
        timeout (int): request timeout
        retries (int): number of retries to attempt
    """
    def __init__(
        self,
        address: str,
        token_url: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        **kwargs: Any
    ) -> None:
        super().__init__(address, **kwargs)
        self.auth = OpenIDAuth(token_url)
        self.client_id = client_id
        self.client_secret = client_secret

        self.access_token = None
        self.refresh_token: Optional[Union[str, bytes]] = refresh_token
        self._get_token()

    def _get_token(self) -> None:
        if self.access_token:
            # check if expired
            try:
                data = self.auth.validate(self.access_token)
                if data['exp'] < time.time()-5:
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
                'client_secret': self.client_secret,
            }

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
                return

        raise Exception('No token available')

    def _prepare(self, *args: Any, **kwargs: Any) -> Tuple[str, Dict[str, Any]]:
        self._get_token()
        if self.access_token:
            self.session.headers['Authorization'] = 'Bearer ' + _to_str(self.access_token)
        return super()._prepare(*args, **kwargs)
