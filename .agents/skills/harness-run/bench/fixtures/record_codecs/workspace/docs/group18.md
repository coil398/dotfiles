# Group 18

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r109

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_109` | decimal | omit | preserve |
| `active_1` | `qty_109` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_109` | enum {"ready": "R109", "held": "H109", "done": "D109"} | required | reject |
| `amount_3` | `mode_109` | scale 2 | omit | preserve |

## r110

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_110` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_110` | enum {"ready": "R110", "held": "H110", "done": "D110"} | default("held") | omit |
| `amount_2` | `flag_110` | scale 2 | required | reject |
| `labels_3` | `mode_110` | strings | omit | preserve |

## r111

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_111` | enum {"ready": "R111", "held": "H111", "done": "D111"} | omit | omit |
| `amount_1` | `qty_111` | scale 2 | default(3) | reject |
| `labels_2` | `flag_111` | strings | required | preserve |
| `title_3` | `mode_111` | text | omit | omit |

## r112

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_112` | scale 2 | omit | omit |
| `labels_1` | `qty_112` | strings | default(["default"]) | reject |
| `title_2` | `flag_112` | text | required | preserve |
| `count_3` | `mode_112` | decimal | omit | omit |

## r113

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_113` | strings | omit | omit |
| `title_1` | `qty_113` | text | default("unset") | reject |
| `count_2` | `flag_113` | decimal | required | preserve |
| `active_3` | `mode_113` | boolean ["yes", "no"] | omit | omit |

## r114

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_114` | text | default("unset") | reject |
| `count_1` | `qty_114` | decimal | required | preserve |
| `active_2` | `flag_114` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_114` | enum {"ready": "R114", "held": "H114", "done": "D114"} | default("held") | reject |
