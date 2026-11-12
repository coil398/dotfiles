from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    kind: str
    value: object
    offset: int

@dataclass(frozen=True)
class Node:
    kind: str
    value: object = None
    children: tuple = ()

@dataclass(frozen=True)
class CompiledPolicy:
    source: str
    tree: Node
