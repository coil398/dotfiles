# Group 04

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r025

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_025` | decimal | default(-7) | reject |
| `active_1` | `qty_025` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_025` | enum {"ready": "R25", "held": "H25", "done": "D25"} | omit | omit |
| `amount_3` | `mode_025` | scale 2 | default(3) | reject |

## r026

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_026` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_026` | enum {"ready": "R26", "held": "H26", "done": "D26"} | required | preserve |
| `amount_2` | `flag_026` | scale 2 | omit | omit |
| `labels_3` | `mode_026` | strings | default(["default"]) | reject |

## r027

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_027` | enum {"ready": "R27", "held": "H27", "done": "D27"} | default("held") | preserve |
| `amount_1` | `qty_027` | scale 2 | required | omit |
| `labels_2` | `flag_027` | strings | omit | reject |
| `title_3` | `mode_027` | text | default("unset") | preserve |

## r028

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_028` | scale 2 | default(3) | preserve |
| `labels_1` | `qty_028` | strings | required | omit |
| `title_2` | `flag_028` | text | omit | reject |
| `count_3` | `mode_028` | decimal | default(-7) | preserve |

## r029

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_029` | strings | default(["default"]) | preserve |
| `title_1` | `qty_029` | text | required | omit |
| `count_2` | `flag_029` | decimal | omit | reject |
| `active_3` | `mode_029` | boolean ["yes", "no"] | default(false) | preserve |

## r030

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_030` | text | required | omit |
| `count_1` | `qty_030` | decimal | omit | reject |
| `active_2` | `flag_030` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_030` | enum {"ready": "R30", "held": "H30", "done": "D30"} | required | omit |
