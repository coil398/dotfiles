"""Sorted per-key range lookup plus global expiration heaps.

Unique ordinals keep keys and payloads out of comparison operations.
"""
from bisect import insort
from heapq import heappush, heappop


class Index:
    def __init__(self, metrics):
        self.buckets = {}
        self.expiry = []
        self.size = 0
        self.metrics = metrics

    def boundary(self, rows, timestamp, upper=False):
        lo, hi = 0, len(rows)
        while lo < hi:
            mid = (lo + hi) // 2
            self.metrics.add("range_probes")
            before = rows[mid][0] <= timestamp if upper else rows[mid][0] < timestamp
            if before:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def candidates(self, key, lower, upper):
        rows = self.buckets.get(key, ())
        start = self.boundary(rows, lower)
        stop = self.boundary(rows, upper, upper=True)
        for _, _, event in rows[start:stop]:
            self.metrics.add("candidate_visits")
            yield event

    def insert(self, event, ordinal):
        insort(self.buckets.setdefault(event.key, []), (event.timestamp, ordinal, event))
        heappush(self.expiry, (event.timestamp, ordinal, event.key))
        self.size += 1

    def expire(self, frontier):
        while self.expiry and self.expiry[0][0] < frontier:
            timestamp, ordinal, key = heappop(self.expiry)
            rows = self.buckets[key]
            # The oldest global entry is also the oldest entry for its key.
            assert rows[0][:2] == (timestamp, ordinal)
            rows.pop(0)
            if not rows:
                del self.buckets[key]
            self.size -= 1
            self.metrics.add("evicted")

    def clear(self):
        self.buckets.clear()
        self.expiry.clear()
        self.size = 0
