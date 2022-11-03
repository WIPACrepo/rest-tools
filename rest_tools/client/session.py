"""Get a `requests`_ Session that fully retries errors.

.. _requests: http://docs.python-requests.org
"""

# fmt:off
# pylint: skip-file

from typing import Iterable

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # type: ignore[import]
from requests_futures.sessions import FuturesSession  # type: ignore[import]


def AsyncSession(
    retries: int = 10,
    backoff_factor: float = 0.3,
    allowed_methods: Iterable[str] = ('HEAD', 'TRACE', 'GET', 'POST', 'PUT', 'OPTIONS', 'DELETE'),
    status_forcelist: Iterable[int] = (408, 429, 500, 502, 503, 504),
) -> FuturesSession:
    """Return a Session object with full retry capabilities.

    Args:
        retries (int): number of retries
        backoff_factor (float): speed factor for retries (in seconds)
        allowed_methods (iterable): http methods to retry on
        status_forcelist (iterable): http status codes to retry on

    Returns:
        :py:class:`requests.Session`: session object
    """
    session = FuturesSession()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        redirect=retries,
        # status=retries,
        allowed_methods=allowed_methods,
        status_forcelist=status_forcelist,
        backoff_factor=backoff_factor,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def Session(
    retries: int = 10,
    backoff_factor: float = 0.3,
    allowed_methods: Iterable[str] = ('HEAD', 'TRACE', 'GET', 'POST', 'PUT', 'OPTIONS', 'DELETE'),
    status_forcelist: Iterable[int] = (408, 429, 500, 502, 503, 504),
) -> requests.Session:
    """Return a Session object with full retry capabilities.

    Args:
        retries (int): number of retries
        backoff_factor (float): speed factor for retries (in seconds)
        allowed_methods (iterable): http methods to retry on
        status_forcelist (iterable): http status codes to retry on

    Returns:
        :py:class:`requests.Session`: session object
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        redirect=retries,
        # status=retries,
        allowed_methods=allowed_methods,
        status_forcelist=status_forcelist,
        backoff_factor=backoff_factor,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
