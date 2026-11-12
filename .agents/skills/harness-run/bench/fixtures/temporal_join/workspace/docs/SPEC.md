# Streaming temporal join contract

## 1. API and validation

Export `Event`, `Match`, `Watermark`, `Flush`, `TemporalJoin`, and `join` from
`temporal_join`. Frozen dataclasses have positional fields:
`Event(side, key, timestamp, value)`, `Match(left, right, timestamp)`,
`Watermark(side, timestamp)`, and `Flush()`.
Construction of messages performs no validation; `push` validates them.
`TemporalJoin(within, lateness=0)` accepts nonnegative integer distances.
Booleans and non-integers raise TypeError; negative distances raise ValueError.
Timestamps may be any integer (including negative and unbounded integers), but
not bool. Keys must be hashable; values may be any Python object and are opaque.
Invalid sides (anything other than strings 'left' and 'right') raise ValueError.
An unhashable event key or non-integer timestamp raises TypeError. Unsupported
push items raise TypeError. Invalid input must leave all state and metrics
unchanged. Message objects and their payloads must not be modified or copied.
Validation precedes lateness filtering. Once closed, RuntimeError takes precedence
for every push, even invalid items or another Flush.

`push(item)` returns a list of Match records. `join(items, within, lateness=0)`
yields exactly the concatenation of those lists, in input order. See section 7
for lazy consumption and termination. No diagnostics are printed by the library.

## 2. Matching and key isolation

Each accepted event matches every previously accepted, still potentially matchable
opposite-side occurrence having an equal key and
`abs(left.timestamp - right.timestamp) <= within`. Both endpoints are included.
Same-side events never match. Python hash/equality semantics apply to keys;
keys are never sorted. Negative and large timestamps work without conversion to
float. Matches hold the original Event objects and have timestamp equal to the
maximum of the two timestamps. Values have no role in key equality or matching.
No watermarks means unbounded history is permitted: out-of-order input is legal.

## 3. Multiplicity and ordering

Duplicate occurrences are retained separately, including repeated pushes of the
same Event object. Every qualifying pair is emitted once, by the push of the
later-arriving member. Each returned list sorts by left timestamp, then right
timestamp, then arrival order of the previously retained member. Values and keys
must never be compared for ordering. Outputs from separate pushes are never
reordered or buffered to produce global event-time order.

## 4. Watermarks and lateness

Each side starts with an unknown watermark. Watermark timestamps are independently
nondecreasing: equality is valid, a decrease raises ValueError atomically.
A watermark emits nothing. An event is late exactly when its timestamp is
strictly less than its own side's watermark minus lateness. Unknown watermark
accepts all timestamps. Late events produce no output and are not retained;
they do not affect ordering. Equality at the acceptance frontier is allowed.
Advancing the other side's watermark never changes this acceptance rule.

## 5. Exact retention and expiration

After every successful push, retain only accepted occurrences for which a future
accepted opposite-side event could still match. For side S with opposite watermark
W, remove events with `timestamp < W - lateness - within`. Equality is retained.
An unknown opposite watermark prevents eviction on S. Eviction uses the opposite
watermark independently; it does not wait for both watermarks or use their minimum.
An incoming event can match existing peers before being immediately discarded by
this retention rule. Absence of future matches is not a reason to suppress these
already-known pairs. Watermark pushes perform expiration before returning.
`engine.retained` is a read-only integer count of retained occurrences on both
sides, not including keys or temporary output records. Empty key buckets must be
removed; `engine.key_count` counts nonempty (side, key) buckets.

## 6. Completion and errors

Flush emits nothing, discards all retained data and key buckets, and permanently
closes the engine (`engine.closed` is True). An empty engine may be flushed.
The next push always raises RuntimeError. There is no outer join or deferred
emission at Flush or at input exhaustion. A finite iterator that exhausts without
Flush simply stops. Separate engines have independent state.

## 7. Single-pass iteration

`join` consumes its input only when advanced. It calls iter(items) once, does not
materialize the input or read ahead past the input causing the current nonempty
batch. If a batch has multiple matches, yield all of them before reading another
input. Stop reading immediately at Flush; ignore trailing items, including errors
or invalid messages. Input iterator exceptions propagate unchanged when reached.
An empty iterable yields no output. The caller may stop after any yield.

## 8. Performance and deterministic instrumentation

Use a per-key temporal range index, not a scan of all retained same-key history.
Expose a read-only `engine.stats` mapping with cumulative integer counters
`range_probes` (timestamp ordering comparisons made to locate interval boundaries),
`candidate_visits` (retained occurrences examined for matching after lookup), and
`evicted` (occurrences removed by watermark retention; Flush does not increment it).
Count actual work, including any candidates rejected by a scan; do not report
estimated counts. Metrics start at zero, continue across Flush, and do not change
on rejected invalid input. `retained` and `key_count` expose live state separately.
A direct scan counts each timestamp predicate as a probe and each examined event
as a candidate visit. Indexed lookup counts every boundary-search comparison and
every returned candidate. Insertion, index maintenance and output sorting are not
range probes. For any event querying a bucket of n occurrences, perform at most
`4 * (n.bit_length() + 1)` boundary comparisons plus `2*k` candidate comparisons
for k matches; visits must equal k for an indexed lookup. Sparse workload acceptance:
8,192 events per side, same key, increasing timestamps spaced by 10 and within=1,
has 8,192 outputs, at most 600,000 probes and at most 16,384 visits. Many-key inputs
must inspect only the incoming key, without comparing heterogeneous keys.
With one or both watermarks advancing after each pair, retained and key_count must
reflect section 5 immediately even over 4,096 unique keys. No wall time is graded.
The required bound concerns comparisons and visited/retained occurrences; sorted
array insertion may shift entries. All input can be traversed only once.
