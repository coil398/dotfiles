# Group 03

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r019

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_019` | decimal | omit | preserve |
| `active_1` | `qty_019` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_019` | enum {"ready": "R19", "held": "H19", "done": "D19"} | required | reject |
| `amount_3` | `mode_019` | scale 10 | omit | preserve |

## r020

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_020` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_020` | enum {"ready": "R20", "held": "H20", "done": "D20"} | default("held") | omit |
| `amount_2` | `flag_020` | scale 10 | required | reject |
| `labels_3` | `mode_020` | strings | omit | preserve |

## r021

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_021` | enum {"ready": "R21", "held": "H21", "done": "D21"} | omit | omit |
| `amount_1` | `qty_021` | scale 10 | default(3) | reject |
| `labels_2` | `flag_021` | strings | required | preserve |
| `title_3` | `mode_021` | text | omit | omit |

## r022

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_022` | scale 10 | omit | omit |
| `labels_1` | `qty_022` | strings | default(["default"]) | reject |
| `title_2` | `flag_022` | text | required | preserve |
| `count_3` | `mode_022` | decimal | omit | omit |

## r023

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_023` | strings | omit | omit |
| `title_1` | `qty_023` | text | default("unset") | reject |
| `count_2` | `flag_023` | decimal | required | preserve |
| `active_3` | `mode_023` | boolean ["yes", "no"] | omit | omit |

## r024

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_024` | text | default("unset") | reject |
| `count_1` | `qty_024` | decimal | required | preserve |
| `active_2` | `flag_024` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_024` | enum {"ready": "R24", "held": "H24", "done": "D24"} | default("held") | reject |
