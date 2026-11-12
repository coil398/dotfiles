# Group 01

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r007

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_007` | decimal | default(-7) | reject |
| `active_1` | `qty_007` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_007` | enum {"ready": "R7", "held": "H7", "done": "D7"} | omit | omit |
| `amount_3` | `mode_007` | scale 10 | default(3) | reject |

## r008

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_008` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_008` | enum {"ready": "R8", "held": "H8", "done": "D8"} | required | preserve |
| `amount_2` | `flag_008` | scale 10 | omit | omit |
| `labels_3` | `mode_008` | strings | default(["default"]) | reject |

## r009

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_009` | enum {"ready": "R9", "held": "H9", "done": "D9"} | default("held") | preserve |
| `amount_1` | `qty_009` | scale 10 | required | omit |
| `labels_2` | `flag_009` | strings | omit | reject |
| `title_3` | `mode_009` | text | default("unset") | preserve |

## r010

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_010` | scale 10 | default(3) | preserve |
| `labels_1` | `qty_010` | strings | required | omit |
| `title_2` | `flag_010` | text | omit | reject |
| `count_3` | `mode_010` | decimal | default(-7) | preserve |

## r011

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_011` | strings | default(["default"]) | preserve |
| `title_1` | `qty_011` | text | required | omit |
| `count_2` | `flag_011` | decimal | omit | reject |
| `active_3` | `mode_011` | boolean ["yes", "no"] | default(false) | preserve |

## r012

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_012` | text | required | omit |
| `count_1` | `qty_012` | decimal | omit | reject |
| `active_2` | `flag_012` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_012` | enum {"ready": "R12", "held": "H12", "done": "D12"} | required | omit |
