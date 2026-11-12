# Batch edits

## 1. API and input

`from tomlkit import apply_edits`. Signature: `apply_edits(document, edits) -> TOMLDocument`.
`document` must be a TOMLDocument, not text or a dict. `edits` is a finite iterable consumed once, in order. Each edit is a dict with exactly these keys:

- `{"op": "set", "path": [...], "value": value}`
- `{"op": "delete", "path": [...]}`
- `{"op": "rename", "path": [...], "new_key": "..."}`

A path is a nonempty list or tuple of string keys and nonnegative integer indices. bool is not an index. Strings are literal keys: dots, quotes, empty strings and Unicode in keys do not split the path. Integer segments address only TOML arrays or arrays of tables; strings address only documents, tables or inline tables. Negative indices and indexing into strings are errors. No implicit intermediate container creation. Set values are TOMLKit-supported native TOML values or Items; existing TOMLKit conversion errors propagate.

## 2. Ordered value semantics

Each edit sees all preceding edits. `set` replaces an existing value, or appends a missing final string key to an existing mapping, using the existing TOMLKit single-assignment conventions. An integer target must already exist; it is never an append. `delete` requires an existing target; array deletion shifts later indices. All intermediate targets must exist and be containers. Values, including tables/inline tables/arrays of tables, retain their normal TOML meaning when serialized and parsed again.

## 3. Rename and layout

`rename` requires an existing final string key in a mapping; it cannot rename an array slot. `new_key` must be a string and must not already exist, including the source name. It is a literal key, not a dotted path. Rename changes the name at the entry's current position, retaining its value, assignment separator, dotted-key status, attached inline comment and leading standalone comments. The new spelling is TOMLKit's default SingleKey spelling (bare when valid, otherwise basic quoted). Other keys keep their spelling. Table and AoT renames update all descendant headers and all physical fragments of split/out-of-order tables, without coalescing or moving fragments. Headers within the renamed subtree may be regenerated from the stored key components, retaining header comments, indentation and line endings. Headers outside that subtree remain byte-identical.

Examples (strings show literal newlines):

```python
apply_edits(parse('a  = 1 # keep\nb=2\n'),
            [{"op":"rename", "path":["a"], "new_key":"x.y"}]).as_string()
# '"x.y"  = 1 # keep\nb=2\n'
apply_edits(parse('a.b = 1\na.c = 2\n'),
            [{"op":"rename", "path":["a"], "new_key":"z"}]).as_string()
# 'z.b = 1\nz.c = 2\n'
```

`set` and `delete` must render exactly like sequential single operations on the original TOMLKit objects; do not reserialize ordinary dicts. This includes existing trivia inheritance and placement rules when a value changes between scalar and table. Unedited byte ranges (including CRLF, comments, quoted keys and whitespace) remain unchanged except for the normal effects of a single operation on its containing array/table. Empty batches preserve every byte.

## 4. Isolation and failures

Never mutate `document`, even if an edit fails partway through the iterable or the iterable raises. Return a distinct TOMLDocument even for an empty batch. It must share no mutable document nodes with the source. Inserted mutable values/Items must also be isolated from the caller. Independent calls share no state. Do not mutate edits or their values. Failures propagate; no partial result is returned.

Invalid document type, non-dict edit, path container/segment type, new_key type or container/segment mismatch raises TypeError. Invalid edit fields or unknown op raises ValueError. Empty path, negative index, rename of an integer slot, existing rename destination raise ValueError. Missing keys raise KeyError (TOMLKit subclasses accepted); out-of-range indices raise IndexError. Error messages are not specified. Iterator exceptions propagate unchanged. The first failing operation stops consumption immediately; no read-ahead.

## 5. Existing API

Preserve parse/dumps/constructors and normal single-edit behavior. The batch API is exported in tomlkit.__all__. No alternate parser, lossy dict round trip, third-party dependency or access to material outside the workspace is required.
