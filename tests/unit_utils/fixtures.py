import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key


@pytest.fixture(scope="session")
def gen_keys():
    priv = generate_private_key(65537, 2048)
    pub = priv.public_key()
    return (priv, pub)


@pytest.fixture(scope="session")
def gen_keys_bytes(gen_keys):
    priv, pub = gen_keys

    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    print(priv_pem, pub_pem)
    return (priv_pem, pub_pem)
