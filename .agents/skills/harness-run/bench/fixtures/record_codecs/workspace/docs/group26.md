# Group 26

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r157

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_157` | decimal | required | omit |
| `active_1` | `qty_157` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_157` | enum {"ready": "R157", "held": "H157", "done": "D157"} | default("held") | preserve |
| `amount_3` | `mode_157` | scale 2 | required | omit |

## r158

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_158` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_158` | enum {"ready": "R158", "held": "H158", "done": "D158"} | omit | reject |
| `amount_2` | `flag_158` | scale 2 | default(3) | preserve |
| `labels_3` | `mode_158` | strings | required | omit |

## r159

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_159` | enum {"ready": "R159", "held": "H159", "done": "D159"} | required | reject |
| `amount_1` | `qty_159` | scale 2 | omit | preserve |
| `labels_2` | `flag_159` | strings | default(["default"]) | omit |
| `title_3` | `mode_159` | text | required | reject |

## r160

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_160` | scale 2 | required | reject |
| `labels_1` | `qty_160` | strings | omit | preserve |
| `title_2` | `flag_160` | text | default("unset") | omit |
| `count_3` | `mode_160` | decimal | required | reject |

## r161

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_161` | strings | required | reject |
| `title_1` | `qty_161` | text | omit | preserve |
| `count_2` | `flag_161` | decimal | default(-7) | omit |
| `active_3` | `mode_161` | boolean ["yes", "no"] | required | reject |

## r162

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_162` | text | omit | preserve |
| `count_1` | `qty_162` | decimal | default(-7) | omit |
| `active_2` | `flag_162` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_162` | enum {"ready": "R162", "held": "H162", "done": "D162"} | omit | preserve |
