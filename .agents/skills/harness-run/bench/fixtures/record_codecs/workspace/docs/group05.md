# Group 05

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r031

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_031` | decimal | required | omit |
| `active_1` | `qty_031` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_031` | enum {"ready": "R31", "held": "H31", "done": "D31"} | default("held") | preserve |
| `amount_3` | `mode_031` | scale 10 | required | omit |

## r032

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_032` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_032` | enum {"ready": "R32", "held": "H32", "done": "D32"} | omit | reject |
| `amount_2` | `flag_032` | scale 10 | default(3) | preserve |
| `labels_3` | `mode_032` | strings | required | omit |

## r033

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_033` | enum {"ready": "R33", "held": "H33", "done": "D33"} | required | reject |
| `amount_1` | `qty_033` | scale 10 | omit | preserve |
| `labels_2` | `flag_033` | strings | default(["default"]) | omit |
| `title_3` | `mode_033` | text | required | reject |

## r034

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_034` | scale 10 | required | reject |
| `labels_1` | `qty_034` | strings | omit | preserve |
| `title_2` | `flag_034` | text | default("unset") | omit |
| `count_3` | `mode_034` | decimal | required | reject |

## r035

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_035` | strings | required | reject |
| `title_1` | `qty_035` | text | omit | preserve |
| `count_2` | `flag_035` | decimal | default(-7) | omit |
| `active_3` | `mode_035` | boolean ["yes", "no"] | required | reject |

## r036

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_036` | text | omit | preserve |
| `count_1` | `qty_036` | decimal | default(-7) | omit |
| `active_2` | `flag_036` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_036` | enum {"ready": "R36", "held": "H36", "done": "D36"} | omit | preserve |
