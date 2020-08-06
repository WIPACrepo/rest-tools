from collections import deque
import statistics
import random
import logging

class RouteStats:
    """
    Route tracking and statistics.

    Keeps track of the last N calls to a route,
    and presents stats on their performance.

    Args:
        num (int): number of past calls to track
        timeout (int): seconds before a request is considered "over time"
    """
    def __init__(self, num=1000, timeout=30):
        self.data = deque(maxlen=num)
        self.timeout = timeout

    def __len__(self):
        return len(self.data)

    def append(self, call_time):
        self.data.append(call_time)

    def clear(self):
        self.data.clear()

    def is_overloaded(self):
        if len(self.data) < 4:
            return False
        median = 0
        try:
            stats = statistics.quantiles(self.data)
            logging.debug('routestats: %r',stats)
            if stats[1] >= self.timeout or stats[2] >= 2*self.timeout:
                median = stats[1]
        except AttributeError:
            med = statistics.median(self.data)
            logging.debug('routestats: %r',med)
            if med >= self.timeout:
                median = med
        return median > 0 and random.random()*median >= self.timeout

    def get_backoff_time(self):
        if len(self.data) < 4:
            return 1
        return int(statistics.median(self.data)*2)
