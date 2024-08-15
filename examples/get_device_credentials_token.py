import argparse
import logging

from rest_tools.client import SavedDeviceGrantAuth


def get_token(address, client_id, client_secret=None, scope=None):
    scopes = scope if scope else []
    rest_client = SavedDeviceGrantAuth(
        address='',
        token_url=address,
        filename='device-refresh-token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    # could use `rest_client` as a `RestClient`, but we're only interested in the token
    return rest_client._openid_token()


def main():
    parser = argparse.ArgumentParser(description='Get an OAuth2 token via client credentials')
    parser.add_argument('--address', default='https://keycloak.icecube.wisc.edu/auth/realms/IceCube', help='OAuth2 server address')
    parser.add_argument('--client_secret', default=None, help='client secret')
    parser.add_argument('--scope', action='append', help='optional scopes')
    parser.add_argument('--log-level', default='info', help='logging level')
    parser.add_argument('client_id', help='client id')

    args = parser.parse_args()
    kwargs = vars(args)

    level = kwargs.pop('log_level').upper()
    logging.basicConfig(level=getattr(logging, level))

    print('access token:', get_token(**kwargs))


if __name__ == '__main__':
    main()
