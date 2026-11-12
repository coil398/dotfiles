Repository: the current working directory, a vendored referencing 0.37.0 package.
Ticket: consecutive reference resolution sometimes selects the wrong schema when nested resources, dynamic anchors, or recursive anchors are involved. Repair resolution while preserving the existing API, immutable resolver behavior, exceptions, and dialect conventions. This is a feature-restoration exercise, not a claim about a historical upstream bug.

Two observed examples:
1. With a root at `https://example.org/root/` and a child schema under `$defs/child` having `$id: "child/"`, resolving `#/$defs/child` and then `leaf` must use `https://example.org/root/child/leaf`.
2. A traversal from an outer resource declaring `$dynamicAnchor: "node"` into an inner resource declaring the same dynamic anchor, followed by `#node`, must select the outer dynamic anchor and keep the resolver usable for later relative lookups.

Read README.md and docs/SPEC.md. The specification and existing tests/docstrings define the contract; support general resource graphs, not just these examples. Allowed changes: referencing/ only. Do not edit public tests or documentation. Do not commit.

Run from the workspace root:
`uv run -q --no-project --with pytest --with attrs==26.1.0 --with rpds-py==2026.9.1 python -m pytest -q tests/`

Return changed files, test results, and anything unverified.
