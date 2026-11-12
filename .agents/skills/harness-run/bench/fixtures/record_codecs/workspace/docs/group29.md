# Group 29

Common rules: [SPEC.md](SPEC.md), especially §§2–5.

## r175

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `count_0` | `v_175` | decimal | required | omit |
| `active_1` | `qty_175` | boolean ["yes", "no"] | omit | reject |
| `state_2` | `flag_175` | enum {"ready": "R175", "held": "H175", "done": "D175"} | default("held") | preserve |
| `amount_3` | `mode_175` | scale 10 | required | omit |

## r176

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `active_0` | `v_176` | boolean ["ON", "OFF"] | required | omit |
| `state_1` | `qty_176` | enum {"ready": "R176", "held": "H176", "done": "D176"} | omit | reject |
| `amount_2` | `flag_176` | scale 10 | default(3) | preserve |
| `labels_3` | `mode_176` | strings | required | omit |

## r177

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `state_0` | `v_177` | enum {"ready": "R177", "held": "H177", "done": "D177"} | required | reject |
| `amount_1` | `qty_177` | scale 10 | omit | preserve |
| `labels_2` | `flag_177` | strings | default(["default"]) | omit |
| `title_3` | `mode_177` | text | required | reject |

## r178

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `amount_0` | `v_178` | scale 10 | required | reject |
| `labels_1` | `qty_178` | strings | omit | preserve |
| `title_2` | `flag_178` | text | default("unset") | omit |
| `count_3` | `mode_178` | decimal | required | reject |

## r179

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `labels_0` | `v_179` | strings | required | reject |
| `title_1` | `qty_179` | text | omit | preserve |
| `count_2` | `flag_179` | decimal | default(-7) | omit |
| `active_3` | `mode_179` | boolean ["yes", "no"] | required | reject |

## r180

| Source | Wire | Conversion | Missing (both directions) | Null (both directions) |
|---|---|---|---|---|
| `title_0` | `v_180` | text | omit | preserve |
| `count_1` | `qty_180` | decimal | default(-7) | omit |
| `active_2` | `flag_180` | boolean ["ON", "OFF"] | required | reject |
| `state_3` | `mode_180` | enum {"ready": "R180", "held": "H180", "done": "D180"} | omit | preserve |
