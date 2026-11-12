# Resolution contract

## 1. Compatibility and ownership

Preserve referencing 0.37.0's public signatures, resource/registry semantics, contents, exception classes and exception attributes/messages. Keep the existing dialect definitions and extension mechanism. No JSON Schema validation is required. Resolvers and registries are persistent values: branching from an earlier resolver and failed lookups cannot mutate it or another branch. Resolution is local to the supplied registry and retriever; do not fetch network resources or delegate resolution to another library. Preserve the existing basic behavior covered by public tests.

## 2. Pointer boundaries

JSON pointers traverse mappings and arrays, percent-decode the fragment and unescape mapping keys (`~1` and `~0`) using the existing conventions. Empty fragments, empty-string keys, array indices and missing paths retain existing results/errors. When pointer traversal reaches a schema subresource, the returned resolver must carry its scope for subsequent lookups. A schema's identifier does not turn arbitrary data into a subresource: the dialect's `maybe_in_subresource` callback determines boundaries. Traversal may cross several boundaries in a single pointer. Subsequent path segments must be interpreted from the newly entered resource boundary, including intervening schemas without identifiers. Custom Specification callbacks remain supported.

## 3. Base URI and dialect

Relative reference and resource identifiers use standard URI joining against the current base, including trailing slashes and absolute identifiers. A pointer result's resolver must resolve later relative references and local fragments against the correct resource. The fragment selects contents but is not part of the base URI. Entering a subresource with no identifier preserves the resolver. Entering one with an identifier joins it to the current base without introducing a reference-traversal history entry. Draft 4 uses `id`; later drafts use `$id`. Keyword sets and dialect transitions follow the existing Specification implementations. Identifiers in arbitrary data (for example inside `enum`) do not change base. Registry aliases, cached/crawled resources and newly retrieved resources must preserve the same lookup semantics.

## 4. Dynamic anchors

In draft 2020-12 a plain anchor is static; only a DynamicAnchor participates in dynamic rebinding. Start at the anchor found in the target resource, then examine dynamic scope in its iteration order. Missing anchors are ignored, as are matching ordinary anchors. Each matching dynamic anchor replaces the selected resource, so the outermost matching dynamic anchor wins. Return both its contents and a resolver entered into that selected resource, so a later relative reference uses its identifier. An anchor can belong to a nested schema and need not be at the resource root. Ordinary anchors do not trigger this search.

## 5. Recursive anchors

For draft 2019-09 `lookup_recursive_ref` resolves `#` first. Only a mapping with a truthy `$recursiveAnchor` permits outward traversal. Visit the caller's dynamic scope in order. Each mapping with a truthy recursive anchor becomes the result; stop at the first boolean/nonmapping or mapping without a truthy recursive anchor. A blocker is not selected. If the initial result is not recursively anchored, return it unchanged. Preserve the resolver paired with the selected result for later lookups. Only the `#` recursive reference is supported by this API.

## 6. Consecutive lookups and dynamic scope

`dynamic_scope()` yields prior base URIs, newest first, paired with the resolver's current registry. A successful reference traversal from a nonempty base records the old base if history is empty or if the destination base differs; a same-base traversal with nonempty history does not duplicate the head. An empty starting base contributes no history. Scope reflects reference traversals, including pointer and anchor lookups, rather than identifier changes made while entering subresources. Preserve all earlier resolver values. A returned resolver must carry the registry produced by retrieval/crawling, so consecutive lookups and anchor lookups reuse retrieved resources. Results and failures must remain consistent when operations are interleaved, repeated, or branched from older states. No special handling of particular URI strings, anchor names, graph depths or lookup sequences is permitted.
