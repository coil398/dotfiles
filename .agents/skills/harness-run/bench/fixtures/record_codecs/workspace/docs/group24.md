# Group 24

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r145

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_145` | decimal | omit | preserve |
| `active_1` | `qty_145` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_145` | enum {"ready": "R145", "held": "H145", "done": "D145"} | required | reject |
| `amount_3` | `mode_145` | scale 2 | omit | preserve |

## r146

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_146` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_146` | enum {"ready": "R146", "held": "H146", "done": "D146"} | default("held") | omit |
| `amount_2` | `flag_146` | scale 2 | required | reject |
| `labels_3` | `mode_146` | strings | omit | preserve |

## r147

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_147` | enum {"ready": "R147", "held": "H147", "done": "D147"} | omit | omit |
| `amount_1` | `qty_147` | scale 2 | default(3) | reject |
| `labels_2` | `flag_147` | strings | required | preserve |
| `title_3` | `mode_147` | text | omit | omit |

## r148

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_148` | scale 2 | omit | omit |
| `labels_1` | `qty_148` | strings | default(["default"]) | reject |
| `title_2` | `flag_148` | text | required | preserve |
| `count_3` | `mode_148` | decimal | omit | omit |

## r149

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_149` | strings | omit | omit |
| `title_1` | `qty_149` | text | default("unset") | reject |
| `count_2` | `flag_149` | decimal | required | preserve |
| `active_3` | `mode_149` | boolean ["yes", "no"] | omit | omit |

## r150

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_150` | text | default("unset") | reject |
| `count_1` | `qty_150` | decimal | required | preserve |
| `active_2` | `flag_150` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_150` | enum {"ready": "R150", "held": "H150", "done": "D150"} | default("held") | reject |
