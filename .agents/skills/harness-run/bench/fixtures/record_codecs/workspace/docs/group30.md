# Group 30

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r181

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_181` | decimal | omit | preserve |
| `active_1` | `qty_181` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_181` | enum {"ready": "R181", "held": "H181", "done": "D181"} | required | reject |
| `amount_3` | `mode_181` | scale 2 | omit | preserve |

## r182

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_182` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_182` | enum {"ready": "R182", "held": "H182", "done": "D182"} | default("held") | omit |
| `amount_2` | `flag_182` | scale 2 | required | reject |
| `labels_3` | `mode_182` | strings | omit | preserve |

## r183

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_183` | enum {"ready": "R183", "held": "H183", "done": "D183"} | omit | omit |
| `amount_1` | `qty_183` | scale 2 | default(3) | reject |
| `labels_2` | `flag_183` | strings | required | preserve |
| `title_3` | `mode_183` | text | omit | omit |

## r184

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_184` | scale 2 | omit | omit |
| `labels_1` | `qty_184` | strings | default(["default"]) | reject |
| `title_2` | `flag_184` | text | required | preserve |
| `count_3` | `mode_184` | decimal | omit | omit |

## r185

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_185` | strings | omit | omit |
| `title_1` | `qty_185` | text | default("unset") | reject |
| `count_2` | `flag_185` | decimal | required | preserve |
| `active_3` | `mode_185` | boolean ["yes", "no"] | omit | omit |

## r186

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_186` | text | default("unset") | reject |
| `count_1` | `qty_186` | decimal | required | preserve |
| `active_2` | `flag_186` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_186` | enum {"ready": "R186", "held": "H186", "done": "D186"} | default("held") | reject |
