# Group 27

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r163

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_163` | decimal | omit | preserve |
| `active_1` | `qty_163` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_163` | enum {"ready": "R163", "held": "H163", "done": "D163"} | required | reject |
| `amount_3` | `mode_163` | scale 10 | omit | preserve |

## r164

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_164` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_164` | enum {"ready": "R164", "held": "H164", "done": "D164"} | default("held") | omit |
| `amount_2` | `flag_164` | scale 10 | required | reject |
| `labels_3` | `mode_164` | strings | omit | preserve |

## r165

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_165` | enum {"ready": "R165", "held": "H165", "done": "D165"} | omit | omit |
| `amount_1` | `qty_165` | scale 10 | default(3) | reject |
| `labels_2` | `flag_165` | strings | required | preserve |
| `title_3` | `mode_165` | text | omit | omit |

## r166

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_166` | scale 10 | omit | omit |
| `labels_1` | `qty_166` | strings | default(["default"]) | reject |
| `title_2` | `flag_166` | text | required | preserve |
| `count_3` | `mode_166` | decimal | omit | omit |

## r167

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_167` | strings | omit | omit |
| `title_1` | `qty_167` | text | default("unset") | reject |
| `count_2` | `flag_167` | decimal | required | preserve |
| `active_3` | `mode_167` | boolean ["yes", "no"] | omit | omit |

## r168

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_168` | text | default("unset") | reject |
| `count_1` | `qty_168` | decimal | required | preserve |
| `active_2` | `flag_168` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_168` | enum {"ready": "R168", "held": "H168", "done": "D168"} | default("held") | reject |
