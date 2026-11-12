# Group 21

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r127

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_127` | decimal | omit | preserve |
| `active_1` | `qty_127` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_127` | enum {"ready": "R127", "held": "H127", "done": "D127"} | required | reject |
| `amount_3` | `mode_127` | scale 10 | omit | preserve |

## r128

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_128` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_128` | enum {"ready": "R128", "held": "H128", "done": "D128"} | default("held") | omit |
| `amount_2` | `flag_128` | scale 10 | required | reject |
| `labels_3` | `mode_128` | strings | omit | preserve |

## r129

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_129` | enum {"ready": "R129", "held": "H129", "done": "D129"} | omit | omit |
| `amount_1` | `qty_129` | scale 10 | default(3) | reject |
| `labels_2` | `flag_129` | strings | required | preserve |
| `title_3` | `mode_129` | text | omit | omit |

## r130

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_130` | scale 10 | omit | omit |
| `labels_1` | `qty_130` | strings | default(["default"]) | reject |
| `title_2` | `flag_130` | text | required | preserve |
| `count_3` | `mode_130` | decimal | omit | omit |

## r131

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_131` | strings | omit | omit |
| `title_1` | `qty_131` | text | default("unset") | reject |
| `count_2` | `flag_131` | decimal | required | preserve |
| `active_3` | `mode_131` | boolean ["yes", "no"] | omit | omit |

## r132

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_132` | text | default("unset") | reject |
| `count_1` | `qty_132` | decimal | required | preserve |
| `active_2` | `flag_132` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_132` | enum {"ready": "R132", "held": "H132", "done": "D132"} | default("held") | reject |
