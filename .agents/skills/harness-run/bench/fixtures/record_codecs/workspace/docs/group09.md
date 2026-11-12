# Group 09

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r055

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_055` | decimal | omit | preserve |
| `active_1` | `qty_055` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_055` | enum {"ready": "R55", "held": "H55", "done": "D55"} | required | reject |
| `amount_3` | `mode_055` | scale 10 | omit | preserve |

## r056

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_056` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_056` | enum {"ready": "R56", "held": "H56", "done": "D56"} | default("held") | omit |
| `amount_2` | `flag_056` | scale 10 | required | reject |
| `labels_3` | `mode_056` | strings | omit | preserve |

## r057

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_057` | enum {"ready": "R57", "held": "H57", "done": "D57"} | omit | omit |
| `amount_1` | `qty_057` | scale 10 | default(3) | reject |
| `labels_2` | `flag_057` | strings | required | preserve |
| `title_3` | `mode_057` | text | omit | omit |

## r058

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_058` | scale 10 | omit | omit |
| `labels_1` | `qty_058` | strings | default(["default"]) | reject |
| `title_2` | `flag_058` | text | required | preserve |
| `count_3` | `mode_058` | decimal | omit | omit |

## r059

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_059` | strings | omit | omit |
| `title_1` | `qty_059` | text | default("unset") | reject |
| `count_2` | `flag_059` | decimal | required | preserve |
| `active_3` | `mode_059` | boolean ["yes", "no"] | omit | omit |

## r060

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_060` | text | default("unset") | reject |
| `count_1` | `qty_060` | decimal | required | preserve |
| `active_2` | `flag_060` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_060` | enum {"ready": "R60", "held": "H60", "done": "D60"} | default("held") | reject |
