# Policy expression contract

## 1. Goal and entry points

Refactor the bundled policy engine into tokenize -> parse -> evaluate, without
changing expression behavior. The package uses only Python's standard library.
The legacy module is the executable behavior reference; this document defines
all supported syntax and API contracts. Implement the pipeline in `policy/`.

Public exports: `tokenize(source)`, `parse(source_or_tokens)`,
`evaluate(source_or_ast, context, *, trace=None, functions=None)`,
`compile_policy(source)`, `check(source, context, ...)`, and
`evaluate_legacy(source, context, ...)`.
`policy.legacy.check` and `policy.legacy.evaluate_legacy` are old entry points;
`policy.compiler.compile_source` is the old compiler entry point.
They must use the new pipeline, not retain a parallel legacy interpreter.
`policy.api.evaluate` must use `policy.api.parse` for strings and
`policy.api.evaluate_tree` for execution. `policy.api.compile_policy` must use
`policy.api.parse` once when compiling, with no reparse during evaluation.
Legacy wrappers and `policy.api.check` / `evaluate_legacy` must call
`policy.api.evaluate` dynamically, so instrumenting that function observes them.
The compiler wrapper calls `policy.api.compile_policy` dynamically.

## 2. Tokens and syntax

Identifiers are ASCII `[A-Za-z_][A-Za-z0-9_]*`. Reserved words (case sensitive)
are `true false null not and or in contains`; longer identifiers are not keywords.
Integers are unsigned decimal digits (leading zeroes allowed). No arithmetic,
floats, attribute access, indexing, negative literals, or implicit coercion.
Whitespace is ignored. `#` outside strings ignores the REST OF SOURCE, including
newlines. Single and double quoted strings may contain Unicode and newlines.
Backslash `n r t` decode to newline, carriage return, tab; every other escaped
character denotes that character (including quotes and backslash).
Unterminated strings/escapes and unsupported characters raise SyntaxError.

`tokenize` returns a tuple of frozen `policy.model.Token(kind, value, offset)`.
Kinds: `literal` for integers, strings, booleans and null; `ident` for identifiers
and operator words; `op` for punctuation and symbolic comparison operators;
`eof` for the sentinel. Values are decoded Python values or operator spelling;
eof value is None. Offsets count Unicode characters from zero in the source;
eof offset equals full source length even after a comment.
Longest symbolic operator wins. Commas need no surrounding whitespace.

## 3. Grammar and AST

The grammar is (alternation is `|`, repetition is `*`, optional is `?`):

```text
expr       := and_expr ('or' and_expr)*
and_expr   := not_expr ('and' not_expr)*
not_expr   := 'not' not_expr | comparison
comparison := atom (('=='|'!='|'<'|'<='|'>'|'>='|'in'|'contains') atom)?
atom       := literal | name | name '(' args? ')' | '(' expr ')'
args       := expr (',' expr)*
```

`not` binds below comparison and above `and`. Binary logic is left associative.
Comparison chains, trailing commas, empty expressions and trailing tokens raise
SyntaxError. Parenthesized comparisons may be compared again. A quoted operator
word or punctuation is always a literal, never syntax. The entire expression is
parsed before any evaluation, including unreachable branches. SyntaxError text
is not contractual, but lexical errors identify the offending character offset.
`parse` accepts source text or the complete token tuple/list returned by tokenize;
input tokens are not mutated. Results are frozen `policy.model.Node` objects:
`Node('literal', value)`, `Node('name', name)`,
`Node('unary', 'not', (child,))`,
`Node('binary', operator, (left, right))`, or
`Node('call', name, tuple(arguments))`. Children are tuples; no extra result nodes.

## 4. Values, names, operators

Names use mapping membership, then subscript lookup. Present None is distinct
from missing. Missing names raise NameError on evaluation. Literal and name
results retain their Python type and object identity. `not` returns bool.
`and` and `or` short circuit and return the selected operand, not a bool.
Every other binary operator evaluates left then right exactly once.
Equality, inequality, ordering, and membership follow Python value semantics,
including bool/int equality and propagated TypeError. `a contains b` is `b in a`;
`a in b` is `a in b`. No copied containers and no type normalization.

## 5. Calls and failures

Calls resolve by membership and lookup in functions only, never context. Resolve
the function BEFORE evaluating its arguments. Unknown functions raise NameError
without evaluating arguments. Supplied noncallables (including None) are resolved
values and raise TypeError when invoked, AFTER evaluating arguments.
Arguments evaluate left-to-right exactly once. The resolved callable is invoked
once, with positional arguments. Its return value retains type and identity.
All runtime exceptions propagate with their original class and object identity.
A skipped logical branch performs no lookups, callbacks or runtime validation.
Syntax errors occur before all lookups/callbacks, even in a skipped branch.

## 6. Trace

Only a list trace (including a list subclass) is used; None or any non-list is
ignored. Preserve existing list contents and append in evaluation order:
`('name', identifier)` AFTER successful lookup;
`('call', function_name)` AFTER successful argument evaluation and immediately
before invocation; `('result', value)` ONCE after a successful whole expression.
No result events for subexpressions. On failure retain the successful prefix,
without a whole-expression result. An invocation that raises still has a call
event. A missing function or failed argument has no call event for that function.
Callbacks may inspect trace to verify event timing.

## 7. Reuse and non-mutation

`compile_policy` returns frozen `CompiledPolicy(source, tree)`; `evaluate` accepts
that object, an AST, or a source string. Each compilation parses once; repeated
evaluations use the stored tree with fresh context/functions/trace and no cached
results. Evaluation does not mutate tokens, AST, context or nested containers,
or functions. Caller callbacks may mutate their own data; the engine adds no
mutations. All entry points preserve result type, identity, exception behavior,
callback counts and trace. No evaluation state is shared between invocations.
