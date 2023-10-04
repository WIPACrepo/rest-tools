"""Test server.stats."""

# fmt:off
# pylint: skip-file

import time

import pytest

# local imports
from rest_tools.server import stats


@pytest.fixture
def random_half(mocker):
    def new_random():
        return 0.5
    mocker.patch('random.random', new_random)


def test_stats_empty():
    s = stats.RouteStats()
    assert not s.is_overloaded()


def test_stats_basic(random_half):
    s = stats.RouteStats(window_size=10, timeout=10)
    for i in range(10):
        s.append(i)
    assert not s.is_overloaded()

    s.clear()
    for i in range(100,110):
        s.append(i)
    assert s.is_overloaded()
    assert 205 < s.get_backoff_time() < 215


def test_stats_expiring(random_half):
    s = stats.RouteStats(window_size=100, window_time=5, timeout=10)

    for i in range(100,105):
        s.append(i)
    time.sleep(5)
    for i in range(10):
        s.append(i)

    assert not s.is_overloaded()
