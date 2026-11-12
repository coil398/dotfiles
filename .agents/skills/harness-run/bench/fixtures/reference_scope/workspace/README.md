# Reference resolution

`referencing/` contains the package. `_core.py` supplies resources, registries and immutable resolvers; `jsonschema.py` supplies JSON Schema dialects and their anchor semantics. `exceptions.py` contains the public exception types. `tests/` contains basic upstream regression tests. Package source includes its public API documentation. The MIT license is in COPYING.

The package does not validate schemas or automatically follow `$ref` fields: consumers explicitly call resolver operations. Resolution rules for this task are in docs/SPEC.md. Dependencies are supplied through the test command in the ticket; no installation of this local package is needed.
