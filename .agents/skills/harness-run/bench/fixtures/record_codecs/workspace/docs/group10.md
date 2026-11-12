# Group 10

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r061

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_061` | decimal | default(-7) | reject |
| `active_1` | `qty_061` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_061` | enum {"ready": "R61", "held": "H61", "done": "D61"} | omit | omit |
| `amount_3` | `mode_061` | scale 2 | default(3) | reject |

## r062

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_062` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_062` | enum {"ready": "R62", "held": "H62", "done": "D62"} | required | preserve |
| `amount_2` | `flag_062` | scale 2 | omit | omit |
| `labels_3` | `mode_062` | strings | default(["default"]) | reject |

## r063

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_063` | enum {"ready": "R63", "held": "H63", "done": "D63"} | default("held") | preserve |
| `amount_1` | `qty_063` | scale 2 | required | omit |
| `labels_2` | `flag_063` | strings | omit | reject |
| `title_3` | `mode_063` | text | default("unset") | preserve |

## r064

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_064` | scale 2 | default(3) | preserve |
| `labels_1` | `qty_064` | strings | required | omit |
| `title_2` | `flag_064` | text | omit | reject |
| `count_3` | `mode_064` | decimal | default(-7) | preserve |

## r065

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_065` | strings | default(["default"]) | preserve |
| `title_1` | `qty_065` | text | required | omit |
| `count_2` | `flag_065` | decimal | omit | reject |
| `active_3` | `mode_065` | boolean ["yes", "no"] | default(false) | preserve |

## r066

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_066` | text | required | omit |
| `count_1` | `qty_066` | decimal | omit | reject |
| `active_2` | `flag_066` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_066` | enum {"ready": "R66", "held": "H66", "done": "D66"} | required | omit |
