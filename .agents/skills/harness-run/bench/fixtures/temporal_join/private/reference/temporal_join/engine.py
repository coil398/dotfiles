"""Symmetric join lifecycle; messages are validated before state changes."""
import logging
from .model import Event, Match, Watermark, Flush
from .validation import distance, integer, side
from .metrics import Metrics
from .index import Index

logger = logging.getLogger(__name__)


class TemporalJoin:
    def __init__(self, within, lateness=0):
        distance(within, "within")
        distance(lateness, "lateness")
        self.within = within
        self.lateness = lateness
        self.watermarks = {"left": None, "right": None}
        self.closed = False
        self._ordinal = 0
        self._metrics = Metrics()
        self._indexes = {s: Index(self._metrics) for s in ("left", "right")}

    @property
    def stats(self):
        return self._metrics.view

    @property
    def retained(self):
        return sum(index.size for index in self._indexes.values())

    @property
    def key_count(self):
        return sum(len(index.buckets) for index in self._indexes.values())

    def push(self, item):
        if self.closed:
            raise RuntimeError("join is closed")
        if isinstance(item, Flush):
            for index in self._indexes.values():
                index.clear()
            self.closed = True
            logger.debug("flush retained=%d", self.retained)
            return []
        if not isinstance(item, (Event, Watermark)):
            raise TypeError("expected Event, Watermark, or Flush")
        side(item.side)
        integer(item.timestamp, "timestamp")
        own = self.watermarks[item.side]
        if isinstance(item, Watermark):
            if own is not None and item.timestamp < own:
                raise ValueError("watermark must be monotonic")
            self.watermarks[item.side] = item.timestamp
            self._evict()
            return []
        hash(item.key)
        if own is not None and item.timestamp < own - self.lateness:
            logger.debug("late side=%s timestamp=%s", item.side, item.timestamp)
            return []
        other = "right" if item.side == "left" else "left"
        peers = list(self._indexes[other].candidates(
            item.key, item.timestamp - self.within, item.timestamp + self.within))
        # The range index orders peers by timestamp then occurrence ordinal.
        matches = []
        for peer in peers:
            left, right = (item, peer) if item.side == "left" else (peer, item)
            matches.append(Match(left, right, max(left.timestamp, right.timestamp)))
        self._ordinal += 1
        self._indexes[item.side].insert(item, self._ordinal)
        self._evict()
        return matches

    def _evict(self):
        for side_name, opposite in (("left", "right"), ("right", "left")):
            watermark = self.watermarks[opposite]
            if watermark is not None:
                self._indexes[side_name].expire(watermark - self.lateness - self.within)
