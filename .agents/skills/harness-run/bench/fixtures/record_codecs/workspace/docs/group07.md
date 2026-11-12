# Group 07

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r043

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_043` | decimal | default(-7) | reject |
| `active_1` | `qty_043` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_043` | enum {"ready": "R43", "held": "H43", "done": "D43"} | omit | omit |
| `amount_3` | `mode_043` | scale 10 | default(3) | reject |

## r044

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_044` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_044` | enum {"ready": "R44", "held": "H44", "done": "D44"} | required | preserve |
| `amount_2` | `flag_044` | scale 10 | omit | omit |
| `labels_3` | `mode_044` | strings | default(["default"]) | reject |

## r045

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_045` | enum {"ready": "R45", "held": "H45", "done": "D45"} | default("held") | preserve |
| `amount_1` | `qty_045` | scale 10 | required | omit |
| `labels_2` | `flag_045` | strings | omit | reject |
| `title_3` | `mode_045` | text | default("unset") | preserve |

## r046

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_046` | scale 10 | default(3) | preserve |
| `labels_1` | `qty_046` | strings | required | omit |
| `title_2` | `flag_046` | text | omit | reject |
| `count_3` | `mode_046` | decimal | default(-7) | preserve |

## r047

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_047` | strings | default(["default"]) | preserve |
| `title_1` | `qty_047` | text | required | omit |
| `count_2` | `flag_047` | decimal | omit | reject |
| `active_3` | `mode_047` | boolean ["yes", "no"] | default(false) | preserve |

## r048

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_048` | text | required | omit |
| `count_1` | `qty_048` | decimal | omit | reject |
| `active_2` | `flag_048` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_048` | enum {"ready": "R48", "held": "H48", "done": "D48"} | required | omit |
