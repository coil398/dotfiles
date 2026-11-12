# Group 22

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r133

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_133` | decimal | default(-7) | reject |
| `active_1` | `qty_133` | boolean ["yes", "no"] | required | preserve |
| `state_2` | `flag_133` | enum {"ready": "R133", "held": "H133", "done": "D133"} | omit | omit |
| `amount_3` | `mode_133` | scale 2 | default(3) | reject |

## r134

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_134` | boolean ["ON", "OFF"] | default(false) | reject |
| `state_1` | `qty_134` | enum {"ready": "R134", "held": "H134", "done": "D134"} | required | preserve |
| `amount_2` | `flag_134` | scale 2 | omit | omit |
| `labels_3` | `mode_134` | strings | default(["default"]) | reject |

## r135

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_135` | enum {"ready": "R135", "held": "H135", "done": "D135"} | default("held") | preserve |
| `amount_1` | `qty_135` | scale 2 | required | omit |
| `labels_2` | `flag_135` | strings | omit | reject |
| `title_3` | `mode_135` | text | default("unset") | preserve |

## r136

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_136` | scale 2 | default(3) | preserve |
| `labels_1` | `qty_136` | strings | required | omit |
| `title_2` | `flag_136` | text | omit | reject |
| `count_3` | `mode_136` | decimal | default(-7) | preserve |

## r137

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_137` | strings | default(["default"]) | preserve |
| `title_1` | `qty_137` | text | required | omit |
| `count_2` | `flag_137` | decimal | omit | reject |
| `active_3` | `mode_137` | boolean ["yes", "no"] | default(false) | preserve |

## r138

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_138` | text | required | omit |
| `count_1` | `qty_138` | decimal | omit | reject |
| `active_2` | `flag_138` | boolean ["ON", "OFF"] | default(false) | preserve |
| `state_3` | `mode_138` | enum {"ready": "R138", "held": "H138", "done": "D138"} | required | omit |
