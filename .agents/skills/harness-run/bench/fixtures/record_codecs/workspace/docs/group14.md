# Group 14

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r085

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_085` | decimal | required | omit |
| `active_1` | `qty_085` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_085` | enum {"ready": "R85", "held": "H85", "done": "D85"} | default("held") | preserve |
| `amount_3` | `mode_085` | scale 2 | required | omit |

## r086

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_086` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_086` | enum {"ready": "R86", "held": "H86", "done": "D86"} | omit | reject |
| `amount_2` | `flag_086` | scale 2 | default(3) | preserve |
| `labels_3` | `mode_086` | strings | required | omit |

## r087

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_087` | enum {"ready": "R87", "held": "H87", "done": "D87"} | required | reject |
| `amount_1` | `qty_087` | scale 2 | omit | preserve |
| `labels_2` | `flag_087` | strings | default(["default"]) | omit |
| `title_3` | `mode_087` | text | required | reject |

## r088

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_088` | scale 2 | required | reject |
| `labels_1` | `qty_088` | strings | omit | preserve |
| `title_2` | `flag_088` | text | default("unset") | omit |
| `count_3` | `mode_088` | decimal | required | reject |

## r089

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_089` | strings | required | reject |
| `title_1` | `qty_089` | text | omit | preserve |
| `count_2` | `flag_089` | decimal | default(-7) | omit |
| `active_3` | `mode_089` | boolean ["yes", "no"] | required | reject |

## r090

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_090` | text | omit | preserve |
| `count_1` | `qty_090` | decimal | default(-7) | omit |
| `active_2` | `flag_090` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_090` | enum {"ready": "R90", "held": "H90", "done": "D90"} | omit | preserve |
