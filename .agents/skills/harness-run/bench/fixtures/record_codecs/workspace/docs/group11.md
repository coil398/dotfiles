# Group 11

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r067

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_067` | decimal | required | omit |
| `active_1` | `qty_067` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_067` | enum {"ready": "R67", "held": "H67", "done": "D67"} | default("held") | preserve |
| `amount_3` | `mode_067` | scale 10 | required | omit |

## r068

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_068` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_068` | enum {"ready": "R68", "held": "H68", "done": "D68"} | omit | reject |
| `amount_2` | `flag_068` | scale 10 | default(3) | preserve |
| `labels_3` | `mode_068` | strings | required | omit |

## r069

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_069` | enum {"ready": "R69", "held": "H69", "done": "D69"} | required | reject |
| `amount_1` | `qty_069` | scale 10 | omit | preserve |
| `labels_2` | `flag_069` | strings | default(["default"]) | omit |
| `title_3` | `mode_069` | text | required | reject |

## r070

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_070` | scale 10 | required | reject |
| `labels_1` | `qty_070` | strings | omit | preserve |
| `title_2` | `flag_070` | text | default("unset") | omit |
| `count_3` | `mode_070` | decimal | required | reject |

## r071

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_071` | strings | required | reject |
| `title_1` | `qty_071` | text | omit | preserve |
| `count_2` | `flag_071` | decimal | default(-7) | omit |
| `active_3` | `mode_071` | boolean ["yes", "no"] | required | reject |

## r072

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_072` | text | omit | preserve |
| `count_1` | `qty_072` | decimal | default(-7) | omit |
| `active_2` | `flag_072` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_072` | enum {"ready": "R72", "held": "H72", "done": "D72"} | omit | preserve |
