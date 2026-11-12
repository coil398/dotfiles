# Group 13

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r079

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_079` | decimal | default(-7) | reject |
| `active_1` | `qty_079` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_079` | enum {"ready": "R79", "held": "H79", "done": "D79"} | omit | omit |
| `amount_3` | `mode_079` | scale 10 | default(3) | reject |

## r080

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_080` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_080` | enum {"ready": "R80", "held": "H80", "done": "D80"} | required | preserve |
| `amount_2` | `flag_080` | scale 10 | omit | omit |
| `labels_3` | `mode_080` | strings | default(["default"]) | reject |

## r081

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_081` | enum {"ready": "R81", "held": "H81", "done": "D81"} | default("held") | preserve |
| `amount_1` | `qty_081` | scale 10 | required | omit |
| `labels_2` | `flag_081` | strings | omit | reject |
| `title_3` | `mode_081` | text | default("unset") | preserve |

## r082

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_082` | scale 10 | default(3) | preserve |
| `labels_1` | `qty_082` | strings | required | omit |
| `title_2` | `flag_082` | text | omit | reject |
| `count_3` | `mode_082` | decimal | default(-7) | preserve |

## r083

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_083` | strings | default(["default"]) | preserve |
| `title_1` | `qty_083` | text | required | omit |
| `count_2` | `flag_083` | decimal | omit | reject |
| `active_3` | `mode_083` | boolean ["yes", "no"] | default(false) | preserve |

## r084

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_084` | text | required | omit |
| `count_1` | `qty_084` | decimal | omit | reject |
| `active_2` | `flag_084` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_084` | enum {"ready": "R84", "held": "H84", "done": "D84"} | required | omit |
