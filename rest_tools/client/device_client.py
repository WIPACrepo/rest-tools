# fmt:off
import io
from itertools import zip_longest
import logging
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

    args = {
        'client_id': client_id,
        'scope': 'offline_access ' + (' '.join(scopes) if scopes else ''),
    }
    if client_secret:
        args['client_secret'] = client_secret

    try:
        r = requests.post(endpoint, data=args)
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
            r = requests.post(auth.token_url, data=args)
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

    refresh_token = req['refresh_token']

    return OpenIDRestClient(address=address, token_url=token_url, client_id=client_id,
                            client_secret=client_secret, refresh_token=refresh_token)
