"""The single event-state transition shared by memory and journal sinks."""
from copy import deepcopy


class ReplicaState:
    def __init__(self):
        self.values = {}
        self.revisions = {}
        self.applied_ids = set()

    def apply(self, event):
        if event["id"] in self.applied_ids:
            return False
        key, revision = event["key"], event["revision"]
        if revision <= self.revisions.get(key, -1):
            self.applied_ids.add(event["id"])
            return False
        self.applied_ids.add(event["id"])
        self.revisions[key] = revision
        if event["op"] == "delete":
            self.values.pop(key, None)
        else:
            self.values[key] = deepcopy(event["value"])
        return True

    def clone(self):
        result = ReplicaState()
        result.values = deepcopy(self.values)
        result.revisions = dict(self.revisions)
        result.applied_ids = set(self.applied_ids)
        return result
