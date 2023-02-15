# fmt:off
import io
from itertools import zip_longest
import logging
from pathlib import Path
import time
from typing import Dict, List, Optional

import qrcode  # type: ignore[import]
import requests

from ..utils.auth import OpenIDAuth
from .openid_client import OpenIDRestClient


def _print_qrcode(req: Dict[str, str]) -> None:
    if 'verification_uri_complete' not in req:
        req['verification_uri_complete'] = req['verification_uri']+'?user_code='+req['user_code']

    qr = qrcode.QRCode(border=2)
    qr.add_data(req['verification_uri_complete'])
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    code = f.read().rstrip().split('\n')
    code_width = max(len(c) for c in code)
    text_width = max(len(req['verification_uri']), 30)
    box_width = 2 + text_width + code_width

    qrtext = f'''
To complete authorization,
scan the QR code or, using
a browser on another device,
visit:
{req["verification_uri"]}

And enter the code:
{req["user_code"]}
'''.split('\n')

    if box_width < 78:
        print('+', '-' * box_width, '+', sep='')
        for text,qrdata in zip_longest(qrtext, code, fillvalue=''):
            print('|  ', f'{text:<{text_width}}', f'{qrdata:{code_width}}', '|', sep='')
        print('+', '-' * box_width, '+', sep='')
    else:
        box_width = max(text_width+4, code_width)
        print('+', '-' * box_width, '+', sep='')
        for text in qrtext:
            print('|  ', f'{text:<{box_width-4}}', '  |', sep='')
        for qrdata in code:
            print('|', f'{qrdata:<{box_width}}', '|', sep='')
        print('+', '-' * box_width, '+', sep='')


def _perform_device_grant(
    logger: logging.Logger,
    device_url: str,
    token_url: str,
    client_id: str,
    client_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
) -> str:
    args = {
        'client_id': client_id,
        'scope': 'offline_access ' + (' '.join(scopes) if scopes else ''),
    }
    if client_secret:
        args['client_secret'] = client_secret

    try:
        r = requests.post(device_url, data=args)
        r.raise_for_status()
        req = r.json()
    except requests.exceptions.HTTPError as exc:
        logger.debug('%r', exc.response.text)
        try:
            req = exc.response.json()
        except Exception:
            req = {}
        error = req.get('error', '')
        raise RuntimeError(f'Device authorization failed: {error}') from exc
    except Exception as exc:
        raise RuntimeError('Device authorization failed') from exc

    logger.debug('Device auth in progress')

    _print_qrcode(req)

    args = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
        'device_code': req['device_code'],
        'client_id': client_id,
    }
    if client_secret:
        args['client_secret'] = client_secret

    sleep_time = int(req.get('interval', 5))
    while True:
        time.sleep(sleep_time)
        try:
            r = requests.post(token_url, data=args)
            r.raise_for_status()
            req = r.json()
        except requests.exceptions.HTTPError as exc:
            logger.debug('%r', exc.response.text)
            try:
                req = exc.response.json()
            except Exception:
                req = {}
            error = req.get('error', '')
            if error == 'authorization_pending':
                continue
            elif error == 'slow_down':
                sleep_time += 5
                continue
            raise RuntimeError(f'Device authorization failed: {error}') from exc
        except Exception as exc:
            raise RuntimeError('Device authorization failed') from exc
        break

    return req['refresh_token']


def DeviceGrantAuth(
    address: str, token_url: str, client_id: str,
    client_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
) -> OpenIDRestClient:
    """A REST client that can handle OpenID and the OAuth2 Device Client flow.

    Args:
        address (str): base address of REST API
        token_url (str): base address of token service
        client_id (str): client id
        client_secret (str): client secret (optional - required for confidential clients)
        scopes (list): token scope list (optional)
    """
    logger = logging.getLogger('DeviceGrantAuth')

    auth = OpenIDAuth(token_url)
    if 'device_authorization_endpoint' not in auth.provider_info:
        raise RuntimeError('Device grant not supported by server')
    endpoint = auth.provider_info['device_authorization_endpoint']

    refresh_token = _perform_device_grant(logger, endpoint, auth.token_url, client_id, client_secret, scopes)

    return OpenIDRestClient(address=address, token_url=token_url, client_id=client_id,
                            client_secret=client_secret, refresh_token=refresh_token)


def _load_token_from_file(filepath: Path) -> Optional[str]:
    if filepath.exists():
        return filepath.read_text()
    return None


def _save_token_to_file(filepath: Path, token: str) -> None:
    filepath.write_text(token)


def SavedDeviceGrantAuth(
    address: str, token_url: str,
    filename: str,
    client_id: str,
    client_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
) -> OpenIDRestClient:
    """
    A REST client that can handle OpenID and the OAuth2 Device Client flow,
    and saves a refresh token to a file for quick access.

    Args:
        address (str): base address of REST API
        token_url (str): base address of token service
        filename (str): name of file to save/load refresh token
        client_id (str): client id
        client_secret (str): client secret (optional - required for confidential clients)
        scopes (list): token scope list (optional)
    """
    logger = logging.getLogger('SavedDeviceGrantAuth')

    filepath = Path(filename)
    refresh_token = _load_token_from_file(filepath)

    if not refresh_token:
        auth = OpenIDAuth(token_url)
        if not auth.provider_info:
            raise RuntimeError('Token service does not support .well-known discovery')
        if 'device_authorization_endpoint' not in auth.provider_info:
            raise RuntimeError('Device grant not supported by server')
        endpoint = auth.provider_info['device_authorization_endpoint']
        refresh_token = _perform_device_grant(logger, endpoint, auth.token_url, client_id, client_secret, scopes)

    def update_func(access, refresh):
        _save_token_to_file(filepath, refresh)

    return OpenIDRestClient(address=address, token_url=token_url, client_id=client_id,
                            client_secret=client_secret, refresh_token=refresh_token,
                            update_func=update_func)
