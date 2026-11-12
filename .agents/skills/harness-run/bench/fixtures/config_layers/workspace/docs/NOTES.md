# Layered configuration

`load(path, *, overrides=None)` reads a JSON object and returns a new merged dictionary. The input files and caller overrides must not be mutated. JSON objects are mappings; arrays, scalars, and null are values, not mappings.

## Includes

A document may contain `$include`, either one path string or a list of path strings. Included files are loaded depth first, in listed order, then the including file is applied. Paths are relative to the file that declares them. Absolute paths are accepted. Includes are transitive. Repeating a file in separate branches is allowed; a file already on the active recursion stack is a cycle and raises `ValueError` with a useful path description. A missing file raises `FileNotFoundError`.

`$include` is loader metadata and never appears in the result. Every loaded document must have a JSON object at its root.

## Merge

Mappings merge recursively. A value from the later layer replaces a scalar, array, or null from an earlier layer. Arrays replace in full; they are never concatenated. Explicit JSON null replaces an earlier value and remains present. The reserved single-key object `{ "$delete": true }` removes that key from the accumulated mapping; deleting an absent key is harmless. Other objects containing `$delete` are ordinary values. Deletion applies at any mapping depth. A later layer can add the same key again.

## Overrides and CLI

`overrides` is the final layer and follows the same merge and deletion rules. `None` means there are no overrides. `load_cli(argv)` accepts `--config PATH` (required) and repeatable `--set dotted.path=JSON_VALUE`. Dotted paths have nonempty components; split at the first `=`. Parse each value with JSON, so `null`, booleans, numbers, arrays, and objects retain their JSON types. Repeated paths apply left to right. A set replaces any scalar or null encountered while descending with a mapping, then sets its leaf. A leaf value can itself be null. Invalid arguments, paths, or JSON produce `ValueError` with a useful diagnostic.
