# Group 28

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r169

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_169` | decimal | default(-7) | reject |
| `active_1` | `qty_169` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_169` | enum {"ready": "R169", "held": "H169", "done": "D169"} | omit | omit |
| `amount_3` | `mode_169` | scale 2 | default(3) | reject |

## r170

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_170` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_170` | enum {"ready": "R170", "held": "H170", "done": "D170"} | required | preserve |
| `amount_2` | `flag_170` | scale 2 | omit | omit |
| `labels_3` | `mode_170` | strings | default(["default"]) | reject |

## r171

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_171` | enum {"ready": "R171", "held": "H171", "done": "D171"} | default("held") | preserve |
| `amount_1` | `qty_171` | scale 2 | required | omit |
| `labels_2` | `flag_171` | strings | omit | reject |
| `title_3` | `mode_171` | text | default("unset") | preserve |

## r172

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_172` | scale 2 | default(3) | preserve |
| `labels_1` | `qty_172` | strings | required | omit |
| `title_2` | `flag_172` | text | omit | reject |
| `count_3` | `mode_172` | decimal | default(-7) | preserve |

## r173

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_173` | strings | default(["default"]) | preserve |
| `title_1` | `qty_173` | text | required | omit |
| `count_2` | `flag_173` | decimal | omit | reject |
| `active_3` | `mode_173` | boolean ["yes", "no"] | default(false) | preserve |

## r174

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_174` | text | required | omit |
| `count_1` | `qty_174` | decimal | omit | reject |
| `active_2` | `flag_174` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_174` | enum {"ready": "R174", "held": "H174", "done": "D174"} | required | omit |
