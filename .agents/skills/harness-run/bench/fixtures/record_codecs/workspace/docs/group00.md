# Group 00

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r001

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_001` | decimal | omit | preserve |
| `active_1` | `qty_001` | boolean ["yes", "no"] | default(false) | omit |
| `state_2` | `flag_001` | enum {"ready": "R1", "held": "H1", "done": "D1"} | required | reject |
| `amount_3` | `mode_001` | scale 2 | omit | preserve |

## r002

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_002` | boolean ["ON", "OFF"] | omit | preserve |
| `state_1` | `qty_002` | enum {"ready": "R2", "held": "H2", "done": "D2"} | default("held") | omit |
| `amount_2` | `flag_002` | scale 2 | required | reject |
| `labels_3` | `mode_002` | strings | omit | preserve |

## r003

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_003` | enum {"ready": "R3", "held": "H3", "done": "D3"} | omit | omit |
| `amount_1` | `qty_003` | scale 2 | default(3) | reject |
| `labels_2` | `flag_003` | strings | required | preserve |
| `title_3` | `mode_003` | text | omit | omit |

## r004

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_004` | scale 2 | omit | omit |
| `labels_1` | `qty_004` | strings | default(["default"]) | reject |
| `title_2` | `flag_004` | text | required | preserve |
| `count_3` | `mode_004` | decimal | omit | omit |

## r005

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_005` | strings | omit | omit |
| `title_1` | `qty_005` | text | default("unset") | reject |
| `count_2` | `flag_005` | decimal | required | preserve |
| `active_3` | `mode_005` | boolean ["yes", "no"] | omit | omit |

## r006

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_006` | text | default("unset") | reject |
| `count_1` | `qty_006` | decimal | required | preserve |
| `active_2` | `flag_006` | boolean ["ON", "OFF"] | omit | omit |
| `state_3` | `mode_006` | enum {"ready": "R6", "held": "H6", "done": "D6"} | default("held") | reject |
