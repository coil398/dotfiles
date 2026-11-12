from types import MappingProxyType


class Metrics:
    def __init__(self):
        self.counts = dict(range_probes=0, candidate_visits=0, evicted=0)
        self.view = MappingProxyType(self.counts)

    def add(self, name, count=1):
        self.counts[name] += count
