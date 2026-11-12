# Group 17

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r103

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_103` | decimal | required | omit |
| `active_1` | `qty_103` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_103` | enum {"ready": "R103", "held": "H103", "done": "D103"} | default("held") | preserve |
| `amount_3` | `mode_103` | scale 10 | required | omit |

## r104

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_104` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_104` | enum {"ready": "R104", "held": "H104", "done": "D104"} | omit | reject |
| `amount_2` | `flag_104` | scale 10 | default(3) | preserve |
| `labels_3` | `mode_104` | strings | required | omit |

## r105

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_105` | enum {"ready": "R105", "held": "H105", "done": "D105"} | required | reject |
| `amount_1` | `qty_105` | scale 10 | omit | preserve |
| `labels_2` | `flag_105` | strings | default(["default"]) | omit |
| `title_3` | `mode_105` | text | required | reject |

## r106

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_106` | scale 10 | required | reject |
| `labels_1` | `qty_106` | strings | omit | preserve |
| `title_2` | `flag_106` | text | default("unset") | omit |
| `count_3` | `mode_106` | decimal | required | reject |

## r107

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_107` | strings | required | reject |
| `title_1` | `qty_107` | text | omit | preserve |
| `count_2` | `flag_107` | decimal | default(-7) | omit |
| `active_3` | `mode_107` | boolean ["yes", "no"] | required | reject |

## r108

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_108` | text | omit | preserve |
| `count_1` | `qty_108` | decimal | default(-7) | omit |
| `active_2` | `flag_108` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_108` | enum {"ready": "R108", "held": "H108", "done": "D108"} | omit | preserve |
