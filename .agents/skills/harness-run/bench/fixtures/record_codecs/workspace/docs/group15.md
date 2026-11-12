# Group 15

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r091

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_091` | decimal | omit | preserve |
| `active_1` | `qty_091` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_091` | enum {"ready": "R91", "held": "H91", "done": "D91"} | required | reject |
| `amount_3` | `mode_091` | scale 10 | omit | preserve |

## r092

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_092` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_092` | enum {"ready": "R92", "held": "H92", "done": "D92"} | default("held") | omit |
| `amount_2` | `flag_092` | scale 10 | required | reject |
| `labels_3` | `mode_092` | strings | omit | preserve |

## r093

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_093` | enum {"ready": "R93", "held": "H93", "done": "D93"} | omit | omit |
| `amount_1` | `qty_093` | scale 10 | default(3) | reject |
| `labels_2` | `flag_093` | strings | required | preserve |
| `title_3` | `mode_093` | text | omit | omit |

## r094

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_094` | scale 10 | omit | omit |
| `labels_1` | `qty_094` | strings | default(["default"]) | reject |
| `title_2` | `flag_094` | text | required | preserve |
| `count_3` | `mode_094` | decimal | omit | omit |

## r095

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_095` | strings | omit | omit |
| `title_1` | `qty_095` | text | default("unset") | reject |
| `count_2` | `flag_095` | decimal | required | preserve |
| `active_3` | `mode_095` | boolean ["yes", "no"] | omit | omit |

## r096

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_096` | text | default("unset") | reject |
| `count_1` | `qty_096` | decimal | required | preserve |
| `active_2` | `flag_096` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_096` | enum {"ready": "R96", "held": "H96", "done": "D96"} | default("held") | reject |
