# Tagged regex

## 1. API and implementation boundary

Implement `tagged_regex/engine.py`: `compile_ast(ast, groups)` returns any internal
program representation; `execute(program, text, full)` returns `None` or a sequence
of `(start, end)` pairs, group 0 first. The completed parser and API in this package
are the integration contract. `compile`, `search` and `fullmatch` accept strings.
Compiled patterns may be reused on independent strings, with no retained match
state. All offsets count Python string characters. Match exposes `span(i=0)`,
`group(i=0)`, `groups(default=None)`, and `string`. Unmatched groups have span
`(-1, -1)` and value `None`. Empty participating groups have span `(p, p)` and
value `''`. No-match is `None`.

Implement the compiler and execution engine yourself, using Python stdlib only.
Delegation to any regular-expression engine is forbidden, including `re`,
`regex`, subprocesses, ctypes/native code, or importing a parser's internal regex
executor. Do not invoke external programs or load serialized answers.

## 2. Grammar and AST

The supplied parser is authoritative for syntax and rejects unsupported syntax
with `ParseError`. Supported operators: literals, `.`, character classes including
ranges and leading `^` negation, concatenation, `|`, capturing parentheses, `*`,
`+`, `?`, and their lazy forms `*?`, `+?`, `??`. Alternation has lowest precedence.
Empty patterns, empty groups and empty alternatives are valid. Backslash quotes
punctuation; `\n`, `\r`, `\t` are supported escapes. Backreferences, special groups,
lookaround, anchors, flags, counted repetition and Unicode character-class escapes
are unsupported. Dot matches every character except newline. Class ranges compare
code points, negated classes also match newline unless excluded explicitly.

AST tuples:

- `('lit', character)`, `('dot',)`, `('class', negated, ((low, high), ...))`
- `('seq', children)`, `('alt', alternatives)` (ordered tuples)
- `('group', number, child)`
- `('repeat', child, quantifier, lazy)`

Group numbers start at 1, in opening-parenthesis order. Group 0 is the whole match.

## 3. Selection and matching

For this grammar the observable results must equal Python 3.13 `re` without flags.
Search chooses the earliest start position, including the position after the last
character for an empty match. At that start, choices are leftmost-first, not
longest: alternatives try their source order. Greedy repeats prefer another
iteration before exit; lazy repeats prefer exit before another iteration.
Fullmatch accepts only a match covering the entire string; it must reconsider
choices when an early success leaves trailing input. Examples:

| pattern | text | search span / groups | fullmatch span / groups |
|---|---|---|---|
| `(a|aa)` | `aa` | `(0,1)` / `('a',)` | `(0,2)` / `('aa',)` |
| `a*?` | `aaa` | `(0,0)` / `()` | `(0,3)` / `()` |
| `(ab|a)b` | `ab` | `(0,2)` / `('a',)` | `(0,2)` / `('a',)` |
| `b*` | `abc` | `(0,0)` / `()` | no match |

## 4. Capture histories and empty repetition

Capture slots are path-specific. Backtracking to another alternative must restore
its prior slots. Repeated captures report the last participating iteration;
a nested group skipped by a later iteration retains its earlier capture.
Groups from an unselected branch remain unmatched. Examples:

- `(a(b)?)+` fullmatching `aba`: groups `('a', 'b')`, spans `(2,3)`, `(1,2)`.
- `(a|(b))*` fullmatching `ba`: groups `('a','b')`, spans `(1,2)`, `(0,1)`.
- `(a?)*` fullmatching `a`: group 1 is `''` at `(1,1)`.
- `(a*)*` fullmatching `aa`: group 1 is `''` at `(2,2)`.
- `(a*?)*?` searching `aa`: group 1 is unmatched, group 0 is empty.

Repeating a nullable expression must terminate. A zero-length iteration may
participate and update captures, but cannot be immediately repeated at the same
position without consuming input. Apply the same ordered choices as Python `re`.

## 5. Scale

Use a compiled program and a bounded-state execution strategy. The supplied
package must handle ambiguous failing repetitions without enumerating every
possible parse. Required families include `(a|aa)*b`, `(a|aa)+b`, `(a?)*b`, lazy
versions, competing search starts, and long successful literal/repetition matches.
Inputs contain up to 12,000 characters, and patterns up to 200 characters with at
most 30 captures. No timing counter supplied by the implementation is trusted.
Tests execute scale workloads in separate processes with a generous calibrated
wall-time limit. Small-input semantics, including nested nullable repeats, remain
required independently of performance.
