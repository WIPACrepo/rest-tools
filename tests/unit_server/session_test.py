import time

import pytest

from rest_tools.server.session import Session, SessionWrapper, redis_available


def _redis_server_up() -> bool:
    """True only if the redis package is installed AND a server answers quickly.

    Avoids long hangs (client retries + backoff) when redis is installed
    but no server is running.
    """
    if not redis_available:
        return False
    import redis
    from redis.backoff import NoBackoff
    from redis.retry import Retry
    try:
        # short timeouts, no retries (redis-py retries by default), so a
        # missing server is detected in ~1s
        conn = redis.Redis(
            socket_connect_timeout=1,
            socket_timeout=1,
            retry=Retry(NoBackoff(), 0),
        )
        try:
            return bool(conn.ping())
        finally:
            conn.close()
    except Exception:
        return False


STORAGE_TYPES = ['memory']
if _redis_server_up():
    STORAGE_TYPES.append('redis')


@pytest.mark.parametrize('storage_type', STORAGE_TYPES)
def test_memory_session(storage_type):
    session_store = Session(storage_type=storage_type, expiration=0.1)

    # Make sure we start with a clear session storage
    session_store.clear()

    # Create a session
    session_store.set('user123', {'username': 'Alice'})

    # Access the session - this will update the last_accessed time and extend expiry
    time.sleep(.03)
    session_data = session_store.get_session('user123')
    assert session_data == {'username': 'Alice'}

    time.sleep(.08)
    # session should still exist
    session_store.get_session('user123')

    time.sleep(.03)
    # Update the session
    session_store.set('user123', {'email': 'alice@example.com'})

    time.sleep(.08)
    # session should still exist
    session_store.get_session('user123')

    # Let the session expire
    time.sleep(.1)
    with pytest.raises(KeyError):
        session_store.get_session('user123')

    # Manual cleanup
    session_store.set('user123', {'username': 'Alice'})
    time.sleep(.11)
    session_store.cleanup_expired_sessions()
    with pytest.raises(KeyError):
        session_store.get_session('user123')

    # Demonstrate deleting a session
    session_store.set('test_session', {'key': 'value'})
    session_store.get_session('test_session')
    session_store.delete_session('test_session')
    with pytest.raises(KeyError):
        session_store.get_session('test_session')

    session_store.close()


@pytest.mark.parametrize('storage_type', STORAGE_TYPES)
def test_session_wrapper(storage_type):
    session_store = Session(storage_type=storage_type, expiration=0.1)

    session_store.set('user123', {'username': 'Alice'})

    data = session_store.get_session('user123')

    data_wrapper = SessionWrapper(key='user123', data=data, session_mgr=session_store)

    time.sleep(.05)
    # should reset expiration
    data_wrapper['foo'] = 'bar'

    time.sleep(.07)
    ret = session_store.get_session('user123')
    assert ret == {'username': 'Alice', 'foo': 'bar'}

    # should reset expiration
    del data_wrapper['foo']

    time.sleep(.07)
    ret = session_store.get_session('user123')
    assert ret == {'username': 'Alice'}

    session_store.close()
