# Group 31

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r187

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_187` | decimal | default(-7) | reject |
| `active_1` | `qty_187` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_187` | enum {"ready": "R187", "held": "H187", "done": "D187"} | omit | omit |
| `amount_3` | `mode_187` | scale 10 | default(3) | reject |

## r188

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_188` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_188` | enum {"ready": "R188", "held": "H188", "done": "D188"} | required | preserve |
| `amount_2` | `flag_188` | scale 10 | omit | omit |
| `labels_3` | `mode_188` | strings | default(["default"]) | reject |

## r189

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_189` | enum {"ready": "R189", "held": "H189", "done": "D189"} | default("held") | preserve |
| `amount_1` | `qty_189` | scale 10 | required | omit |
| `labels_2` | `flag_189` | strings | omit | reject |
| `title_3` | `mode_189` | text | default("unset") | preserve |

## r190

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_190` | scale 10 | default(3) | preserve |
| `labels_1` | `qty_190` | strings | required | omit |
| `title_2` | `flag_190` | text | omit | reject |
| `count_3` | `mode_190` | decimal | default(-7) | preserve |

## r191

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_191` | strings | default(["default"]) | preserve |
| `title_1` | `qty_191` | text | required | omit |
| `count_2` | `flag_191` | decimal | omit | reject |
| `active_3` | `mode_191` | boolean ["yes", "no"] | default(false) | preserve |

## r192

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_192` | text | required | omit |
| `count_1` | `qty_192` | decimal | omit | reject |
| `active_2` | `flag_192` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_192` | enum {"ready": "R192", "held": "H192", "done": "D192"} | required | omit |
