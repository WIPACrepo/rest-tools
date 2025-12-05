"""
Session storage.

Memory is usually for testing.

Redis is for production, and ideal when mulitple servers are running.
"""

from collections.abc import MutableMapping
from collections import UserDict
import dataclasses as dc
from enum import Enum
import logging
import time
from typing import Iterator, Union

from tornado.web import RequestHandler


SessionData = MutableMapping[str, str]


# Define the structure of the internal session representation
@dc.dataclass(frozen=True)
class SessionEntry:
    data: SessionData
    expiration: float


# Define the session storage type
class SessionStorage(MutableMapping[str, SessionEntry]):
    def close(self):
        ...


class MemorySessionStorage(UserDict[str, SessionEntry], SessionStorage):
    """
    In-memory session storage.

    This is just a dict, and is designed for testing.
    """
    def close(self):
        pass


try:
    import redis
    from redis.cache import CacheConfig
    from redis.commands.search.field import TextField
    from redis.commands.search.index_definition import IndexDefinition, IndexType
    from redis.backoff import ExponentialBackoff
    from redis.retry import Retry
    import redis.exceptions
    redis_available = True
except ImportError:
    redis_available = False
else:
    class RedisSessionStorage(SessionStorage):
        """
        Redis-backed session storage.

        Ideal for production, where multiple servers could be running at the same time.
        """
        def __init__(self, host='localhost', username=None, password=None, ssl=False):
            retry = Retry(ExponentialBackoff(), 5)
            self._conn = redis.Redis(
                host=host,
                username=username,
                password=password,
                ssl=ssl,
                cache_config=CacheConfig(),
                decode_responses=True,
                protocol=3,
                retry=retry,
            )
            self._conn.ping()
            try:
                self._conn.ft('idx:key').info()
            except redis.exceptions.ResponseError as e:
                if 'Unknown Index Name' in str(e):
                    schema = (
                        TextField('key'),
                    )
                    # Create the index
                    self._conn.ft('idx:key').create_index(
                        schema,  # type: ignore
                        definition=IndexDefinition(
                            prefix=['session:'], index_type=IndexType.HASH
                        )
                    )

        def close(self):
            self._conn.close()

        def __getitem__(self, key: str) -> SessionEntry:
            ret: dict = self._conn.hgetall('session:'+key)  # type: ignore
            if not ret:
                raise KeyError()
            exp = float(ret.pop('_expiration'))
            return SessionEntry(data=ret, expiration=exp)

        def __setitem__(self, key: str, value: SessionEntry):
            data = {'_expiration': value.expiration}
            data.update(value.data)  # type: ignore
            # we delete first to clear extra keys not in the new data
            self._conn.delete('session:'+key)
            self._conn.hset('session:'+key, mapping=data)

        def __delitem__(self, key: str):
            self._conn.delete('session:'+key)

        def __iter__(self) -> Iterator:
            for key in self._conn.keys('session:*'):  # type: ignore
                yield key[8:]

        def __len__(self) -> int:
            return self._conn.dbsize()  # type: ignore


class StorageTypes(Enum):
    MEMORY = 'memory'
    REDIS = 'redis'


class Session:
    """
    Session storage with expiration.
    """
    _sessions: SessionStorage

    def __init__(self, storage_type: Union[str, StorageTypes] = 'memory', expiration: float = 1800, **kwargs):
        """
        Initializes the session store.

        Args:
            expiration: The time in seconds after which a session will expire
                        due to inactivity. Defaults to 1800 (30 minutes).
        """
        st = StorageTypes(storage_type)
        if st == StorageTypes.MEMORY:
            self._sessions = MemorySessionStorage()
        elif st == StorageTypes.REDIS:
            if not redis_available:
                logging.error("You have asked to use the redis session storage backend, but "
                              "`redis` is not installed. Install it with `pip install redis`.")
                raise RuntimeError('redis package not installed')
            self._sessions = RedisSessionStorage(**kwargs)
        else:
            raise RuntimeError("Invalid session storage type")

        self._expiration = expiration

    def close(self):
        self._sessions.close()

    def set(self, session_id: str, data: SessionData):
        """
        Creates a new session or overwrite an existing session.

        Args:
            session_id (str):   The unique identifier for the session.
            data (SessionData): The initial data to store in the session.
        """
        session_data = SessionEntry(
            data=data if data is not None else {},
            expiration=time.time() + self._expiration,
        )
        self._sessions[session_id] = session_data

    def get_session(self, session_id: str) -> SessionData:
        """
        Retrieves a session by its ID.

        Args:
            session_id (str): The ID of the session to retrieve.

        Returns:
            SessionData: The session data if the session exists and is not expired, otherwise None.

        Raises:
            KeyError: If the session does not exist.
        """
        session: SessionEntry = self._sessions[session_id]
        current_time = time.time()
        if current_time < session.expiration:
            session = dc.replace(session, expiration=current_time + self._expiration)
            self._sessions[session_id] = session
            return session.data
        else:
            del self._sessions[session_id]
            raise KeyError('session does not exist')

    def delete_session(self, session_id: str) -> bool:
        """
        Deletes a session by its ID.

        Args:
            session_id (str): The ID of the session to delete.

        Returns:
            bool: True if the session was deleted,
                  False if the session did not exist.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def cleanup_expired_sessions(self) -> None:
        """
        Manually cleans up expired sessions from the store.
        """
        current_time: float = time.time()
        expired_session_ids: list[str] = [
            session_id
            for session_id, session in self._sessions.items()
            if current_time >= session.expiration
        ]
        for session_id in expired_session_ids:
            del self._sessions[session_id]

    def clear(self) -> None:
        """
        Clear all session data.
        """
        for session_id in self._sessions:
            del self._sessions[session_id]


class SessionWrapper(SessionData):
    """Wrap session with nice setter to auto-update session."""
    def __init__(self, key: str, data: SessionData, session_mgr: Session):
        self._key = key
        self._session_mgr = session_mgr
        self._data = data

    def __getitem__(self, name: str) -> str:
        return self._data[name]

    def __setitem__(self, name: str, value: str):
        self._data[name] = value
        self._session_mgr.set(self._key, self._data)

    def __delitem__(self, name: str):
        del self._data[name]
        self._session_mgr.set(self._key, self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


class SessionMixin(RequestHandler):
    """Mixin to access session data"""
    def initialize(self, *args, session: Session, **kwargs):
        self._session_mgr = session
        super().initialize(*args, **kwargs)

    @property
    def session(self):
        if self.current_user:
            try:
                data = self._session_mgr.get_session(self.current_user)
            except KeyError:
                data = {}
                self._session_mgr.set(self.current_user, data)

            return SessionWrapper(
                self.current_user,
                data,
                self._session_mgr
            )
        else:
            return None
