# Group 06

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r037

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_037` | decimal | omit | preserve |
| `active_1` | `qty_037` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_037` | enum {"ready": "R37", "held": "H37", "done": "D37"} | required | reject |
| `amount_3` | `mode_037` | scale 2 | omit | preserve |

## r038

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_038` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_038` | enum {"ready": "R38", "held": "H38", "done": "D38"} | default("held") | omit |
| `amount_2` | `flag_038` | scale 2 | required | reject |
| `labels_3` | `mode_038` | strings | omit | preserve |

## r039

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_039` | enum {"ready": "R39", "held": "H39", "done": "D39"} | omit | omit |
| `amount_1` | `qty_039` | scale 2 | default(3) | reject |
| `labels_2` | `flag_039` | strings | required | preserve |
| `title_3` | `mode_039` | text | omit | omit |

## r040

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_040` | scale 2 | omit | omit |
| `labels_1` | `qty_040` | strings | default(["default"]) | reject |
| `title_2` | `flag_040` | text | required | preserve |
| `count_3` | `mode_040` | decimal | omit | omit |

## r041

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_041` | strings | omit | omit |
| `title_1` | `qty_041` | text | default("unset") | reject |
| `count_2` | `flag_041` | decimal | required | preserve |
| `active_3` | `mode_041` | boolean ["yes", "no"] | omit | omit |

## r042

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_042` | text | default("unset") | reject |
| `count_1` | `qty_042` | decimal | required | preserve |
| `active_2` | `flag_042` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_042` | enum {"ready": "R42", "held": "H42", "done": "D42"} | default("held") | reject |
