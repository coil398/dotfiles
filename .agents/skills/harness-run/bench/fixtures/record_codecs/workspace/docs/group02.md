# Group 02

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r013

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_013` | decimal | required | omit |
| `active_1` | `qty_013` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_013` | enum {"ready": "R13", "held": "H13", "done": "D13"} | default("held") | preserve |
| `amount_3` | `mode_013` | scale 2 | required | omit |

## r014

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_014` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_014` | enum {"ready": "R14", "held": "H14", "done": "D14"} | omit | reject |
| `amount_2` | `flag_014` | scale 2 | default(3) | preserve |
| `labels_3` | `mode_014` | strings | required | omit |

## r015

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_015` | enum {"ready": "R15", "held": "H15", "done": "D15"} | required | reject |
| `amount_1` | `qty_015` | scale 2 | omit | preserve |
| `labels_2` | `flag_015` | strings | default(["default"]) | omit |
| `title_3` | `mode_015` | text | required | reject |

## r016

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_016` | scale 2 | required | reject |
| `labels_1` | `qty_016` | strings | omit | preserve |
| `title_2` | `flag_016` | text | default("unset") | omit |
| `count_3` | `mode_016` | decimal | required | reject |

## r017

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_017` | strings | required | reject |
| `title_1` | `qty_017` | text | omit | preserve |
| `count_2` | `flag_017` | decimal | default(-7) | omit |
| `active_3` | `mode_017` | boolean ["yes", "no"] | required | reject |

## r018

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_018` | text | omit | preserve |
| `count_1` | `qty_018` | decimal | default(-7) | omit |
| `active_2` | `flag_018` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_018` | enum {"ready": "R18", "held": "H18", "done": "D18"} | omit | preserve |
