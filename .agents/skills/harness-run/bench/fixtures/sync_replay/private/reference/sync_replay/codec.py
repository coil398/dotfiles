"""JSON representation of durable replica state, including tombstones."""
from copy import deepcopy
from .state import ReplicaState


def encode_state(state):
    return {"values": deepcopy(state.values),
            "revisions": dict(state.revisions),
            "applied_ids": sorted(state.applied_ids)}


def decode_state(data):
    state = ReplicaState()
    state.values = deepcopy(data["values"])
    state.revisions = dict(data["revisions"])
    state.applied_ids = set(data["applied_ids"])
    return state
