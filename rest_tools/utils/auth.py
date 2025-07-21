"""auth.py."""

# fmt:off

import logging
import time
from typing import Any, Optional, Union

import jwt
import requests

LOGGER = logging.getLogger(__name__)


class _AuthValidate:
    def __init__(self, audience=None, issuers=None, algorithms=None, leeway=60):
        self.audience = audience
        self.issuers = issuers
        self.algorithms = algorithms if algorithms else ['RS256','RS512']
        self.leeway = leeway

    def _validate(self, token, key, **kwargs):
        options = {}

        # required claims
        claims = ['exp', 'iat', 'iss']
        claims.extend(kwargs.pop('required', []))
        options['require'] = claims

        leeway = kwargs.pop('leeway', None)
        if leeway is None:
            leeway = self.leeway
        leeway = float(leeway)

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

        token = jwt.decode(token, key, leeway=leeway, algorithms=self.algorithms, options=options, **kwargs)
        if issuers and token['iss'] not in issuers:
            raise jwt.exceptions.InvalidIssuerError()

        return token


class Auth(_AuthValidate):
    """
    Handle authentication of JWT tokens.
    """

    def __init__(self, secret, pub_secret=None, issuer='IceProd', algorithm='HS512', expiration=31622400, integer_times=False, **kwargs):
        if 'algorithms' not in kwargs:
            kwargs['algorithms'] = [algorithm]
        super().__init__(**kwargs)
        self.secret = secret
        self.pub_secret = pub_secret if pub_secret else secret
        self.issuer = issuer
        self.algorithm = algorithm
        self.max_exp = expiration
        self.integer_times = integer_times

    def create_token(self, subject, expiration=None, payload=None, headers=None):
        """
        Create a token.

        Args:
            subject (str): the user or other owner
            expiration (int): duration in seconds for which the token is valid
            payload (dict): any other fields that should be included

        Returns:
            str: representation of JWT token
        """
        exp = self.max_exp
        if expiration and exp > expiration:
            exp = expiration
        now = time.time()
        if self.integer_times:
            now = int(now)
            exp = int(exp)
        if not payload:
            payload = {}
        payload.update({
            'iss': self.issuer,
            'sub': subject,
            'exp': now+exp,
            'nbf': now,
            'iat': now,
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
        return self._validate(token, self.pub_secret, issuer=self.issuer, **kwargs)


class OpenIDAuth(_AuthValidate):
    """Handle validation of JWT tokens using OpenID .well-known auto-discovery."""

    def __init__(
        self,
        url: str,
        provider_info: Optional[dict[str, Union[str, list[str]]]] = None,
        public_keys: Optional[dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.url = url if url.endswith('/') else url+'/'
        self.public_keys = public_keys if public_keys else {}
        self.provider_info: dict[str, Any] = provider_info if provider_info else {}
        self.token_url = ""

        if public_keys and provider_info:
            self._allow_refresh = False
        else:
            self._allow_refresh = True
            self._refresh_keys()

    def _refresh_keys(self):
        if not self._allow_refresh:
            LOGGER.warning('no refresh of keys is allowed')
            return
        try:
            if not self.provider_info:
                # discovery
                r = requests.get(self.url+'.well-known/openid-configuration')
                r.raise_for_status()
                self.provider_info = r.json()

                # get token url
                self.token_url = self.provider_info['token_endpoint']

            # get keys
            if self.provider_info['jwks_uri']:
                LOGGER.debug('refreshing keys')
                r = requests.get(self.provider_info['jwks_uri'])
                r.raise_for_status()
                LOGGER.debug('certs: %r', r.json())
                self.public_keys = {
                    k.key_id: k.key for k in jwt.PyJWKSet.from_dict(r.json()).keys
                }
                LOGGER.debug('keys: %r', self.public_keys)
            else:
                LOGGER.debug('not refreshing keys because provider_info incomplete')
        except Exception:
            LOGGER.warning('failed to refresh OpenID keys', exc_info=True)

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
