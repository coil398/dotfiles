# Group 23

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r139

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_139` | decimal | required | omit |
| `active_1` | `qty_139` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_139` | enum {"ready": "R139", "held": "H139", "done": "D139"} | default("held") | preserve |
| `amount_3` | `mode_139` | scale 10 | required | omit |

## r140

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_140` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_140` | enum {"ready": "R140", "held": "H140", "done": "D140"} | omit | reject |
| `amount_2` | `flag_140` | scale 10 | default(3) | preserve |
| `labels_3` | `mode_140` | strings | required | omit |

## r141

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_141` | enum {"ready": "R141", "held": "H141", "done": "D141"} | required | reject |
| `amount_1` | `qty_141` | scale 10 | omit | preserve |
| `labels_2` | `flag_141` | strings | default(["default"]) | omit |
| `title_3` | `mode_141` | text | required | reject |

## r142

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_142` | scale 10 | required | reject |
| `labels_1` | `qty_142` | strings | omit | preserve |
| `title_2` | `flag_142` | text | default("unset") | omit |
| `count_3` | `mode_142` | decimal | required | reject |

## r143

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_143` | strings | required | reject |
| `title_1` | `qty_143` | text | omit | preserve |
| `count_2` | `flag_143` | decimal | default(-7) | omit |
| `active_3` | `mode_143` | boolean ["yes", "no"] | required | reject |

## r144

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_144` | text | omit | preserve |
| `count_1` | `qty_144` | decimal | default(-7) | omit |
| `active_2` | `flag_144` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_144` | enum {"ready": "R144", "held": "H144", "done": "D144"} | omit | preserve |
