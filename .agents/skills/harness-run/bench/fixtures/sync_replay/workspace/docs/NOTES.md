# Checkpointed sync specification

## 1. Entry points and valid inputs

Import the APIs from `sync_replay`. `SyncEngine(source, sink, checkpoint,
page_size=100).run()` fetches from `checkpoint.load()` and runs until a terminal
page. `page_size` is retained for callers and does not slice pages or change the
source's `fetch(cursor)` signature. No automatic retry occurs within a run.
Events are dictionaries with nonempty string `id`, string `key` (empty is legal),
nonnegative integer `revision` (bool is invalid), `op` of `put` or `delete`.
A put requires `value`; any JSON value including null is allowed. Extra fields
are ignored, including `after`. `validate_event` returns a deep copy and raises
ValueError for malformed events. Both sinks validate before changing state,
even for a known id. Valid sources have finite acyclic cursor chains.

## 2. Source addressing and delivery

`FakeSource(pages)` takes `(events, next_cursor)` pairs in chain order. Fetch
None returns page 0. Fetch the preceding page's next_cursor returns the next
page. Cursors are opaque strings, including the empty string and Unicode; only
None means terminal. Intermediate pages may be empty. The last page must be
terminal; a single terminal page and an empty source are legal. Duplicate or
ambiguous chain addresses raise ValueError at construction. Unknown cursors
raise KeyError. `calls` records fetch arguments in order, including failures.
Input pages are snapshotted at construction, and each fetch returns a fresh
deep copy. Repeated fetches return the same page without consuming it.
Events can be redelivered within a page, across pages, or across engine instances.
Custom sources implement this same fetch protocol; they may raise exceptions.

## 3. Global event identity

Sink idempotency persists for the sink's entire lifetime, across runs and keys.
A previously seen id returns False without changing values or revisions, even
if its repeated payload differs. A valid stale event's id is also recorded.
An id ignored as stale cannot later apply under another key or revision.
An applied event returns True exactly when it wins the revision comparison;
a higher revision with an identical visible value still counts as applied.

## 4. Revision ordering

Events are applied in listed order. Each key has its own revision floor,
initially -1. Only a strictly greater revision wins. Equal revisions use
first-writer-wins, including put/delete ties. Do not sort events by revision.
Keys, revisions, and ids are separate namespaces. Revision zero is valid.
`run()` returns the number of True results in that invocation only, including
successful deletes of absent keys, and excluding duplicates and stale events.

## 5. Deletes and recreation

A winning delete removes the visible key, retains its revision tombstone,
and records its id. Deleting an absent key still establishes a tombstone.
A stale or equal revision put cannot resurrect a deleted key. A strictly newer
put recreates it; subsequent deletes follow the same rules. Put null is a
present key with null value, distinguishable from absence using snapshot().

## 6. Failure and page acknowledgement

Every sink apply is atomic. On failure the failing event changes neither ids,
revisions nor values. Earlier successful events remain applied. Fetch, apply,
and checkpoint save exceptions propagate unchanged. A page is acknowledged
by saving its next_cursor only after ALL events have returned (True or False).
Save once per page, including empty pages and terminal pages (save None).
No later page is fetched after any exception. If checkpoint save raises,
already applied events remain, the old checkpoint remains, and replay is safe.
Checkpoint implementations/custom stores promise a failed save leaves the old
cursor. Do not attempt rollback of successfully applied events or checkpoint.

`FailingSink(sink, fail_at)` raises OSError before delegating its 1-based Nth
apply call, exactly once. Its calls counter includes duplicate and stale calls;
later calls work. fail_at must be a positive int, excluding bool.

## 7. Resume and durable stores

Restart using the same sink state and checkpoint, possibly new engine/source
instances. Resume fetches exactly the stored cursor. None is both the initial
and terminal cursor: running after completion replays from the beginning and
returns zero if all events have been seen. A terminal page is never skipped.
`MemoryCheckpoint(cursor=None)` exposes cursor and a history list of successful
save arguments. `FileCheckpoint(path)` starts at None if missing, saves JSON
atomically and survives reconstruction. `JournalSink(path)` uses a JSON state
snapshot, retaining values, tombstones AND ids (including stale ids) across
reconstruction. A failed JSON serialization or file replace leaves disk and
memory unchanged. Journal and file checkpoint paths are separate; their parent
directories may not exist. Test fixtures use local temporary files only.

## 8. Ownership and observation

No API mutates input dictionaries or nested values. MemorySink and JournalSink
own their stored values. get(key), snapshot(), and values return detached deep
copies. revisions returns a fresh dict and applied_ids a fresh set. Observing
or mutating these results cannot change sink state. Missing get returns None.
MemorySink(), MemoryCheckpoint(), and independent file paths do not share state.
The package uses only stdlib, no network, no sleeping or wall-clock decisions.
Logs use the library logger without installing handlers or exposing payloads.
