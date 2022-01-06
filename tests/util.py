import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key


@pytest.fixture
def port():
    """Get an ephemeral port number."""
    # https://unix.stackexchange.com/a/132524
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    addr = s.getsockname()
    ephemeral_port = addr[1]
    s.close()
    return ephemeral_port

@pytest.fixture
async def server(monkeypatch, port, make_token):
    monkeypatch.setenv('DEBUG', 'True')
    monkeypatch.setenv('PORT', str(port))

    monkeypatch.setenv('ISSUERS', 'issuer')
    monkeypatch.setenv('AUDIENCE', 'aud')
    monkeypatch.setenv('BASE_PATH', '/base')

    s = None

    def fn(scope):
        token = make_token(scope, 'issuer', 'aud')
        return RestClient(f'http://localhost:{port}', token=token, timeout=0.1, retries=0)

    try:
        yield fn
    finally:
        await s.stop()

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
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print(priv_pem, pub_pem)
    return (priv_pem, pub_pem)
