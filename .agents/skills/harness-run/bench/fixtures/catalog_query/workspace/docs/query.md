# Catalog query specification

## 1. API and ownership

`Catalog(records=())` consumes an iterable of JSON object mappings once, deep-copies
it, and preserves insertion order. Records contain finite JSON numbers, strings,
booleans, nulls, arrays and nested mappings. `records` returns a tuple of detached
record copies. Search results are detached copies too: changing input, results,
or `records` must not affect future queries. Duplicates are retained.

`Query.parse(text)` and `parse(text)` return a reusable `Query`.
`QueryError` subclasses `ValueError`. `Catalog.search(query='', *, sort=None,
offset=0, limit=None)` accepts text or `Query` and returns a list.
`Catalog.search_page(query='', *, sort=None, offset=0, limit=20)` returns exactly
`{"items": [...], "total": N, "offset": O, "limit": L}`. Total counts matches
before slicing. An empty/whitespace query matches all records. A parsed query can
be reused across catalogs and calls. Invalid query types raise `ValueError`, even
on an empty catalog or a zero-sized page.

## 2. Grammar and precedence

```text
query      := or_expr | whitespace
or_expr    := and_expr (OR and_expr)*
and_expr   := atom (AND atom)*
atom       := '(' or_expr ')' | comparison
comparison := field operator value
operator   := ':' | '=' | '!=' | '>' | '>=' | '<' | '<='
value      := bare | single_quoted | double_quoted
field      := segment ('.' segment)*
segment    := [A-Za-z_][A-Za-z0-9_]*
```

AND/OR are case-insensitive; AND binds more tightly. Parentheses override
precedence and may nest. Whitespace is optional around operators/parentheses;
whitespace between adjacent bare tokens separates them. No implicit AND, NOT,
functions, or lists are supported. Bare AND/OR are reserved as values (quote them
to match those strings); they may be field names. A bare token ends at whitespace
or any of `():=!<>"'`. All input must be consumed. Empty parentheses, missing
operands, malformed fields/operators, unmatched parentheses, extra tokens and
unterminated strings raise `QueryError`, including when there are no records.

## 3. Quotes and literals

Single and double quotes delimit strings; their contents may include Unicode,
whitespace, keywords, parentheses and operator symbols. Backslash escapes only
backslash, single quote and double quote, in either quote style. Other escapes
(including `\n`) and a trailing backslash are errors. A quote inside a bare token
starts a new token, so `name:ab"cd"` is invalid, not string concatenation.

Quoted values are always strings (including `"null"`, `"12"`, `"true"`). Bare
`null`, `true`, `false` are case-insensitive typed literals. Numbers match
`[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?`.
An integer without decimal/exponent is an int; other numbers are floats. Numeric
queries are restricted to finite values. Other bare values are strings, including
hyphens, Unicode and tokens such as `1x`. No string/number coercion is performed.

## 4. Field lookup and equality

Dotted paths traverse mappings only. A missing segment or non-mapping parent
makes the path missing. A literal dotted key does not override traversal.
Missing is distinct from explicit null and matches **no** comparison, including
`!=`. `:`, `=`, and `!=` mean equality/equality/inequality, not substring search.
Strings use Unicode casefold equality. Int and float form one numeric type;
boolean is separate, so `true` does not equal `1`. Other values compare only
within their type. Explicit null equals bare null, not the string `"null"`.
Present values of incompatible types are unequal and therefore match `!=`.

## 5. Relational operators

`>`, `>=`, `<`, `<=` accept two numbers (int/float, excluding bool) or two
strings. Strings compare case-sensitively by Python Unicode lexicographic order.
Missing, null, booleans, containers or incompatible types never match any
relational comparison. Numeric and string comparisons can be combined in the
same expression. No coercion occurs.

## 6. Sorting

`sort` is None, a comma-separated string, or a list/tuple of field strings.
Prefix a field with one `-` for descending. An empty list/tuple means no sort;
an empty string or invalid field raises `ValueError`. No whitespace trimming,
empty comma members, `+`, doubled `-`, empty path segments or non-string fields
are accepted. Other sort argument types raise `ValueError`. Validate even on
empty/no-match results. Fields use the grammar in section 2.

Filter first; sort matching records by keys in the listed order (first key is
primary). Each key compares scalar types in this ascending order:
null < boolean (false < true) < number < string < missing.
Numbers compare numerically, strings case-sensitively. Reverse this complete
order for a descending key. Sorting a matching record with an array/mapping
at a requested key raises `ValueError`. Nonmatching records are not sorted.
Ties retain insertion order even in descending sorts; duplicate records remain.

## 7. Pagination and validation

Apply filter, sort, offset, then limit, in that order. Offset is a nonnegative
int; limit is None or a nonnegative int for search. Page limit must be an int.
Booleans are not ints here. Invalid pagination raises `ValueError`, including
on empty inputs. Zero limit returns no items but still validates query and sort.
Offsets beyond the end return an empty list while total remains the match count.
Page metadata echoes the validated offset and limit. Calls do not retain cursor
state. Slicing must not change catalog insertion order.

## 8. CLI

`python -m catalog PATH [QUERY] [--sort FIELDS] [--offset N] [--limit N] [--page]`
reads a UTF-8 JSON array of objects. Query defaults to empty; offset to 0; CLI
limit to 20. Normal output is one JSON array; `--page` returns the page object
from section 1 with identical semantics to the API. Unicode must round-trip.
Use `--sort=-field` for descending fields. Success exits 0. File/JSON/record,
query, sort and pagination errors exit 2 with a diagnostic on stderr and no JSON
on stdout. Argument errors also exit 2. No traceback is required. Each invocation
is independent. The CLI must actually call the catalog query implementation.
