import argparse
import asyncio
import logging

from rest_tools.client import SavedDeviceGrantAuth
from rest_tools.client.openid_client import RegisterOpenIDClient


async def get_token(address, scope=None):
    scopes = scope if scope else []
    async with RegisterOpenIDClient(address, 'test') as (client_id, client_secret):
        rest_client = SavedDeviceGrantAuth(
            address='',
            token_url=address,
            filename='token-issuer-refresh-token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
        )
        # could use `rest_client` as a `RestClient`, but we're only interested in the token
        return rest_client._openid_token()


def main():
    parser = argparse.ArgumentParser(description='Get an OAuth2 token via client credentials')
    parser.add_argument('--address', default='https://keycloak.icecube.wisc.edu/auth/realms/IceCube', help='OAuth2 server address')
    parser.add_argument('--scope', action='append', help='optional scopes')
    parser.add_argument('--log-level', default='info', help='logging level')

    args = parser.parse_args()
    kwargs = vars(args)

    level = kwargs.pop('log_level').upper()
    logging.basicConfig(level=getattr(logging, level))

    logging.info('scopes: %r', kwargs['scope'])

    print(asyncio.run(get_token(**kwargs)))


if __name__ == '__main__':
    main()
