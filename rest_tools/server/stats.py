"""Route stats."""


# fmt:off

import logging
import random
import statistics
import time
from collections import deque


class RouteStats:
    """
    Route tracking and statistics.

    Keeps track of the last N calls to a route,
    and presents stats on their performance.

    Args:
        window_size (int): number of past calls to track
        window_time (int): number of seconds to keep track of past calls
        timeout (int): seconds before a request is considered "over time"
    """
    def __init__(self, window_size=1000, window_time=3600, timeout=30):
        self.data = deque(maxlen=window_size)
        self.times = deque(maxlen=window_size)
        self.window_size = window_size
        self.window_time = window_time
        self.timeout = timeout

    def __len__(self):
        return len(self.data)

    def append(self, call_time):
        self.data.append(call_time)
        self.times.append(time.time())

    def clear(self):
        self.data.clear()
        self.times.clear()

    def is_overloaded(self):
        # check window time
        window_cutoff = time.time()-self.window_time
        i = 0
        for i,t in enumerate(self.times):
            if t >= window_cutoff:
                break
        if i > 0:
            logging.debug('routestats: removing %d entries due to age', i)
            self.data = deque((self.data[j] for j in range(i,len(self.data))), maxlen=self.window_size)
            self.times = deque((self.times[j] for j in range(i,len(self.times))), maxlen=self.window_size)

        # check if we have enough data to form stats
        if len(self.data) < 4:
            return False

        # now check stats
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
