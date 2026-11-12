# Group 12

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r073

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_073` | decimal | omit | preserve |
| `active_1` | `qty_073` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_073` | enum {"ready": "R73", "held": "H73", "done": "D73"} | required | reject |
| `amount_3` | `mode_073` | scale 2 | omit | preserve |

## r074

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_074` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_074` | enum {"ready": "R74", "held": "H74", "done": "D74"} | default("held") | omit |
| `amount_2` | `flag_074` | scale 2 | required | reject |
| `labels_3` | `mode_074` | strings | omit | preserve |

## r075

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_075` | enum {"ready": "R75", "held": "H75", "done": "D75"} | omit | omit |
| `amount_1` | `qty_075` | scale 2 | default(3) | reject |
| `labels_2` | `flag_075` | strings | required | preserve |
| `title_3` | `mode_075` | text | omit | omit |

## r076

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_076` | scale 2 | omit | omit |
| `labels_1` | `qty_076` | strings | default(["default"]) | reject |
| `title_2` | `flag_076` | text | required | preserve |
| `count_3` | `mode_076` | decimal | omit | omit |

## r077

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_077` | strings | omit | omit |
| `title_1` | `qty_077` | text | default("unset") | reject |
| `count_2` | `flag_077` | decimal | required | preserve |
| `active_3` | `mode_077` | boolean ["yes", "no"] | omit | omit |

## r078

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_078` | text | default("unset") | reject |
| `count_1` | `qty_078` | decimal | required | preserve |
| `active_2` | `flag_078` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_078` | enum {"ready": "R78", "held": "H78", "done": "D78"} | default("held") | reject |
