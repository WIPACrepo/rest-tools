# fmt:off
# pylint: skip-file

import json
import logging
import time

import jwt
import requests


class _AuthValidate:
    def __init__(self, audience=None, issuers=None, algorithms=None):
        self.audience = audience
        self.issuers = issuers
        self.algorithms = algorithms if algorithms else ['RS256','RS512']

    def _validate(self, token, key, **kwargs):
        options = {}

        # required claims
        claims = ['exp', 'iat', 'iss']
        claims.extend(kwargs.pop('require', []))
        options['require'] = claims

        # configure the audience to validate
        audience = kwargs.pop('audience', None)
        if not audience:
            audience = self.audience
        if not audience:
            options['verify_aud'] = False
        else:
            if isinstance(audience, str):
                audience = [audience]
            kwargs['audience'] = audience

        # configure issuers to validate
        issuers = kwargs.pop('issuers', None)
        if not issuers:
            iss = kwargs.pop('issuer', None)
            if iss:
                issuers = [iss]
            else:
                issuers = self.issuers

        token = jwt.decode(token, key, algorithms=self.algorithms, options=options, **kwargs)
        if issuers and token['iss'] not in issuers:
            raise jwt.exceptions.InvalidIssuerError()

        return token


class Auth(_AuthValidate):
    """
    Handle authentication of JWT tokens.
    """

    def __init__(self, secret, pub_secret=None, issuer='IceProd', algorithm='HS512', expiration=31622400, expiration_temp=86400, **kwargs):
        if 'algorithms' not in kwargs:
            kwargs['algorithms'] = [algorithm]
        super().__init__(**kwargs)
        self.secret = secret
        self.pub_secret = pub_secret if pub_secret else secret
        self.issuer = issuer
        self.algorithm = algorithm
        self.max_exp = expiration
        self.max_exp_temp = expiration_temp

    def create_token(self, subject, expiration=None, type='temp', payload=None, headers=None):
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

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm, headers=headers)
        return token

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
        return self._validate(token, self.pub_secret, issuer=self.issuer, required=['type'], **kwargs)


class OpenIDAuth(_AuthValidate):
    """Handle validation of JWT tokens using OpenID .well-known auto-discovery."""
    def __init__(self, url, **kwargs):
        super().__init__(**kwargs)
        self.url = url if url.endswith('/') else url+'/'
        self.public_keys = {}
        self.provider_info = {}
        self.token_url = None

        self._refresh_keys()

    def _refresh_keys(self):
        try:
            if not self.provider_info:
                # discovery
                r = requests.get(self.url+'.well-known/openid-configuration')
                r.raise_for_status()
                self.provider_info = r.json()

                # get token url
                self.token_url = self.provider_info['token_endpoint']

            # get keys
            r = requests.get(self.provider_info['jwks_uri'])
            r.raise_for_status()
            for jwk in r.json()['keys']:
                logging.debug(f'jwk: {jwk}')
                kid = jwk['kid']
                logging.info(f'loaded JWT key {kid}')
                self.public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        except Exception:
            logging.warning('failed to refresh OpenID keys', exc_info=True)

    def validate(self, token, **kwargs):
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
            return self._validate(token, key, **kwargs)
        else:
            raise Exception(f'JWT key {header["kid"]} not found')
