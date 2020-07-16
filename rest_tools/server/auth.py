import json
import logging
import time

import jwt
import requests


class Auth:
    """
    Handle authentication of JWT tokens.
    """
    
    def __init__(self, secret, pub_secret=None, issuer='IceProd', algorithm='HS512', expiration=31622400, expiration_temp=86400):
        self.secret = secret
        self.pub_secret = pub_secret if pub_secret else secret
        self.issuer = issuer
        self.algorithm = algorithm
        self.max_exp = expiration
        self.max_exp_temp = expiration_temp

    def create_token(self, subject, expiration=None, type='temp', payload=None):
        """
        Create a token.

        Args:
            subject (str): the user or other owner
            expiration (int): duration in seconds for which the token is valid
            type (str): type of token
            payload (dict): any other fields that should be included

        Returns:
            str: representation of JWT token
        """
        exp = self.max_exp_temp if type == 'temp' else self.max_exp
        if expiration and exp > expiration:
            exp = expiration
        now = time.time()
        if not payload:
            payload = {}
        payload.update({
            'iss': self.issuer,
            'sub': subject,
            'exp': now+exp,
            'nbf': now,
            'iat': now,
            'type': type,
        })
        return jwt.encode(payload, self.secret, algorithm=self.algorithm).decode('utf-8')

    def validate(self, token, **kwargs):
        """
        Validate a token.

        Args:
            token (str): a JWT token
            **kwargs: additional args passed directly to jwt.decode

        Returns:
            dict: data inside token

        Raises:
            Exception on failure to validate.
        """
        try:
            ret = jwt.decode(token, self.pub_secret, issuer=self.issuer, algorithms=[self.algorithm], **kwargs)
        except jwt.exceptions.InvalidAudienceError:
            if 'audience' not in kwargs:
                kwargs['audience'] = ['ANY']
                ret = jwt.decode(token, self.pub_secret, issuer=self.issuer, algorithms=[self.algorithm], **kwargs)
            else:
                raise
        if 'type' not in ret:
            raise Exception('no type information')
        return ret


class OpenIDAuth:
    """Handle validation of JWT tokens using OpenID .well-known auto-discovery."""
    def __init__(self, url):
        self.url = url if url.endswith('/') else url+'/'
        self.public_keys = {}
        self.token_url = None

        self._refresh_keys()

    def _refresh_keys(self):
        try:
            # discovery
            r = requests.get(self.url+'.well-known/openid-configuration')
            r.raise_for_status()
            provider_info = r.json()

            # get token url
            self.token_url = provider_info['token_endpoint']

            # get keys
            r = requests.get(provider_info['jwks_uri'])
            r.raise_for_status()
            for jwk in r.json()['keys']:
                kid = jwk['kid']
                logging.info(f'loaded JWT key {kid}')
                self.public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        except Exception:
            logging.warning('failed to refresh OpenID keys', exc_info=True)

    def validate(self, token, audience=None):
        """
        Validate a token.

        Args:
            token (str): a JWT token
            audience (str): audience, or None to disable audience verification

        Returns:
            dict: data inside token

        Raises:
            Exception on failure to validate.
        """
        header = jwt.get_unverified_header(token)
        if header['kid'] not in self.public_keys:
            self._refresh_keys()
        if header['kid'] in self.public_keys:
            key = self.public_keys[header['kid']]
            options = {}
            kwargs = {}
            if not audience:
                options['verify_aud'] = False
            elif audience.lower() == 'any':
                kwargs['audience'] = ['ANY']
            else:
                kwargs['audience'] = [audience]
            return jwt.decode(token, key, algorithms=['RS256','RS512'], options=options, **kwargs)
        else:
            raise Exception(f'JWT key {header["kid"]} not found')
