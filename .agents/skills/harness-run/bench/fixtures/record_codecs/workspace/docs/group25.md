# Group 25

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r151

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_151` | decimal | default(-7) | reject |
| `active_1` | `qty_151` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_151` | enum {"ready": "R151", "held": "H151", "done": "D151"} | omit | omit |
| `amount_3` | `mode_151` | scale 10 | default(3) | reject |

## r152

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_152` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_152` | enum {"ready": "R152", "held": "H152", "done": "D152"} | required | preserve |
| `amount_2` | `flag_152` | scale 10 | omit | omit |
| `labels_3` | `mode_152` | strings | default(["default"]) | reject |

## r153

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_153` | enum {"ready": "R153", "held": "H153", "done": "D153"} | default("held") | preserve |
| `amount_1` | `qty_153` | scale 10 | required | omit |
| `labels_2` | `flag_153` | strings | omit | reject |
| `title_3` | `mode_153` | text | default("unset") | preserve |

## r154

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_154` | scale 10 | default(3) | preserve |
| `labels_1` | `qty_154` | strings | required | omit |
| `title_2` | `flag_154` | text | omit | reject |
| `count_3` | `mode_154` | decimal | default(-7) | preserve |

## r155

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_155` | strings | default(["default"]) | preserve |
| `title_1` | `qty_155` | text | required | omit |
| `count_2` | `flag_155` | decimal | omit | reject |
| `active_3` | `mode_155` | boolean ["yes", "no"] | default(false) | preserve |

## r156

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_156` | text | required | omit |
| `count_1` | `qty_156` | decimal | omit | reject |
| `active_2` | `flag_156` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_156` | enum {"ready": "R156", "held": "H156", "done": "D156"} | required | omit |
