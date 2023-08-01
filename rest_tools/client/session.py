"""Get a `requests`_ Session that fully retries errors.

.. _requests: http://docs.python-requests.org
"""

# fmt:off
# pylint: skip-file

from typing import Collection

import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession  # type: ignore[import]
from urllib3.util.retry import Retry


def AsyncSession(
    retries: int,
    backoff_factor: float,
    allowed_methods: Collection[str] = ('HEAD', 'TRACE', 'GET', 'POST', 'PUT', 'OPTIONS', 'DELETE'),
    status_forcelist: Collection[int] = (408, 429, 500, 502, 503, 504),
) -> FuturesSession:
    """Return a Session object with full retry capabilities.

    Args:
        retries (int): number of retries
        backoff_factor (float): speed factor for retries (in seconds)
        allowed_methods (collection): http methods to retry on
        status_forcelist (collection): http status codes to retry on

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
    retries: int,
    backoff_factor: float,
    allowed_methods: Collection[str] = ('HEAD', 'TRACE', 'GET', 'POST', 'PUT', 'OPTIONS', 'DELETE'),
    status_forcelist: Collection[int] = (408, 429, 500, 502, 503, 504),
) -> requests.Session:
    """Return a Session object with full retry capabilities.

    Args:
        retries (int): number of retries
        backoff_factor (float): speed factor for retries (in seconds)
        allowed_methods (collection): http methods to retry on
        status_forcelist (collection): http status codes to retry on

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
