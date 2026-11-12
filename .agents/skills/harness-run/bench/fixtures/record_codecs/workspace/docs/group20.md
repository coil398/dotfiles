# Group 20

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r121

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_121` | decimal | required | omit |
| `active_1` | `qty_121` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_121` | enum {"ready": "R121", "held": "H121", "done": "D121"} | default("held") | preserve |
| `amount_3` | `mode_121` | scale 2 | required | omit |

## r122

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_122` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_122` | enum {"ready": "R122", "held": "H122", "done": "D122"} | omit | reject |
| `amount_2` | `flag_122` | scale 2 | default(3) | preserve |
| `labels_3` | `mode_122` | strings | required | omit |

## r123

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_123` | enum {"ready": "R123", "held": "H123", "done": "D123"} | required | reject |
| `amount_1` | `qty_123` | scale 2 | omit | preserve |
| `labels_2` | `flag_123` | strings | default(["default"]) | omit |
| `title_3` | `mode_123` | text | required | reject |

## r124

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_124` | scale 2 | required | reject |
| `labels_1` | `qty_124` | strings | omit | preserve |
| `title_2` | `flag_124` | text | default("unset") | omit |
| `count_3` | `mode_124` | decimal | required | reject |

## r125

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_125` | strings | required | reject |
| `title_1` | `qty_125` | text | omit | preserve |
| `count_2` | `flag_125` | decimal | default(-7) | omit |
| `active_3` | `mode_125` | boolean ["yes", "no"] | required | reject |

## r126

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_126` | text | omit | preserve |
| `count_1` | `qty_126` | decimal | default(-7) | omit |
| `active_2` | `flag_126` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_126` | enum {"ready": "R126", "held": "H126", "done": "D126"} | omit | preserve |
