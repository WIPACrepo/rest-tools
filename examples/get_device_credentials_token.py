import argparse

from rest_tools.client import SavedDeviceGrantAuth


def get_token(address, client_id):
    rest_client = SavedDeviceGrantAuth('', token_url=address, filename='device-refresh-token', client_id=client_id)
    # could use `rest_client` as a `RestClient`, but we're only interested in the token
    return rest_client._openid_token()


def main():
    parser = argparse.ArgumentParser(description='Get an OAuth2 token via client credentials')
    parser.add_argument('--address', default='https://keycloak.icecube.wisc.edu/auth/realms/IceCube', help='OAuth2 server address')
    parser.add_argument('client_id', help='client id')

    args = parser.parse_args()
    kwargs = vars(args)
    print('access token:', get_token(**kwargs))

if __name__ == '__main__':
    main()
