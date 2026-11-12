# Group 08

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r049

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_049` | decimal | required | omit |
| `active_1` | `qty_049` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_049` | enum {"ready": "R49", "held": "H49", "done": "D49"} | default("held") | preserve |
| `amount_3` | `mode_049` | scale 2 | required | omit |

## r050

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_050` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_050` | enum {"ready": "R50", "held": "H50", "done": "D50"} | omit | reject |
| `amount_2` | `flag_050` | scale 2 | default(3) | preserve |
| `labels_3` | `mode_050` | strings | required | omit |

## r051

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_051` | enum {"ready": "R51", "held": "H51", "done": "D51"} | required | reject |
| `amount_1` | `qty_051` | scale 2 | omit | preserve |
| `labels_2` | `flag_051` | strings | default(["default"]) | omit |
| `title_3` | `mode_051` | text | required | reject |

## r052

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_052` | scale 2 | required | reject |
| `labels_1` | `qty_052` | strings | omit | preserve |
| `title_2` | `flag_052` | text | default("unset") | omit |
| `count_3` | `mode_052` | decimal | required | reject |

## r053

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_053` | strings | required | reject |
| `title_1` | `qty_053` | text | omit | preserve |
| `count_2` | `flag_053` | decimal | default(-7) | omit |
| `active_3` | `mode_053` | boolean ["yes", "no"] | required | reject |

## r054

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_054` | text | omit | preserve |
| `count_1` | `qty_054` | decimal | default(-7) | omit |
| `active_2` | `flag_054` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_054` | enum {"ready": "R54", "held": "H54", "done": "D54"} | omit | preserve |
