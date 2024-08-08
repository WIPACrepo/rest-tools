import base64
import hashlib
import secrets
from typing import MutableMapping

from cachetools import TTLCache


class PKCEMixin:
    _pkcs_challenges: MutableMapping[str, str] = TTLCache(maxsize=10000, ttl=3600)

    @classmethod
    def create_pkce_challenge(cls) -> str:
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').split('=')[0]
        cls._pkcs_challenges[code_challenge] = code_verifier
        return code_challenge

    @classmethod
    def get_pkce_verifier(cls, challenge: str) -> str:
        if challenge in cls._pkcs_challenges:
            return cls._pkcs_challenges[challenge]
        raise KeyError('invalid pkce challenge')
