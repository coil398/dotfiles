# Group 16

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r097

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_097` | decimal | default(-7) | reject |
| `active_1` | `qty_097` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_097` | enum {"ready": "R97", "held": "H97", "done": "D97"} | omit | omit |
| `amount_3` | `mode_097` | scale 2 | default(3) | reject |

## r098

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_098` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_098` | enum {"ready": "R98", "held": "H98", "done": "D98"} | required | preserve |
| `amount_2` | `flag_098` | scale 2 | omit | omit |
| `labels_3` | `mode_098` | strings | default(["default"]) | reject |

## r099

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_099` | enum {"ready": "R99", "held": "H99", "done": "D99"} | default("held") | preserve |
| `amount_1` | `qty_099` | scale 2 | required | omit |
| `labels_2` | `flag_099` | strings | omit | reject |
| `title_3` | `mode_099` | text | default("unset") | preserve |

## r100

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_100` | scale 2 | default(3) | preserve |
| `labels_1` | `qty_100` | strings | required | omit |
| `title_2` | `flag_100` | text | omit | reject |
| `count_3` | `mode_100` | decimal | default(-7) | preserve |

## r101

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_101` | strings | default(["default"]) | preserve |
| `title_1` | `qty_101` | text | required | omit |
| `count_2` | `flag_101` | decimal | omit | reject |
| `active_3` | `mode_101` | boolean ["yes", "no"] | default(false) | preserve |

## r102

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_102` | text | required | omit |
| `count_1` | `qty_102` | decimal | omit | reject |
| `active_2` | `flag_102` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_102` | enum {"ready": "R102", "held": "H102", "done": "D102"} | required | omit |
