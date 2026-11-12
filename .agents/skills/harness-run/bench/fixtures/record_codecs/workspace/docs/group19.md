# Group 19

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r115

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_115` | decimal | default(-7) | reject |
| `active_1` | `qty_115` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_115` | enum {"ready": "R115", "held": "H115", "done": "D115"} | omit | omit |
| `amount_3` | `mode_115` | scale 10 | default(3) | reject |

## r116

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_116` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_116` | enum {"ready": "R116", "held": "H116", "done": "D116"} | required | preserve |
| `amount_2` | `flag_116` | scale 10 | omit | omit |
| `labels_3` | `mode_116` | strings | default(["default"]) | reject |

## r117

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_117` | enum {"ready": "R117", "held": "H117", "done": "D117"} | default("held") | preserve |
| `amount_1` | `qty_117` | scale 10 | required | omit |
| `labels_2` | `flag_117` | strings | omit | reject |
| `title_3` | `mode_117` | text | default("unset") | preserve |

## r118

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_118` | scale 10 | default(3) | preserve |
| `labels_1` | `qty_118` | strings | required | omit |
| `title_2` | `flag_118` | text | omit | reject |
| `count_3` | `mode_118` | decimal | default(-7) | preserve |

## r119

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_119` | strings | default(["default"]) | preserve |
| `title_1` | `qty_119` | text | required | omit |
| `count_2` | `flag_119` | decimal | omit | reject |
| `active_3` | `mode_119` | boolean ["yes", "no"] | default(false) | preserve |

## r120

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_120` | text | required | omit |
| `count_1` | `qty_120` | decimal | omit | reject |
| `active_2` | `flag_120` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_120` | enum {"ready": "R120", "held": "H120", "done": "D120"} | required | omit |
