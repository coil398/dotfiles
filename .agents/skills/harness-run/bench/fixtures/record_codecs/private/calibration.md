# record_codecs calibration

Artifacts: `/home/coil398/.ai-pir-runs/benchv2/record-codecs-calibration-2bfvxwxa`. Reproduce with `uv run /home/coil398/dotfiles/.agents/skills/harness-run/bench/fixtures/record_codecs/private/calibrate.py`.

Construction source: `private/build.py`; regenerate with `uv run private/build.py` from the fixture root. The private source emits workspace docs, stubs, reference and literal tests. No candidate implementation is used to compute any expected value.

## Harness self-check

`python3 /home/coil398/dotfiles/.agents/skills/harness-run/bench/bench.py --self-check --tasks record_codecs --out /home/coil398/.ai-pir-runs/benchv2/record-codecs-calibration-2bfvxwxa/self-check`

| fixture | reference public | reference hidden | baseline hidden |
|---|---:|---:|---:|
| record_codecs | 194/194 | 768/768 | 0/768 |

## Offline grading and structure

All manual grading runs copy pristine workspace, overlay reference only where requested, then copy private/tests into tests_hidden. Both suites use the harness command with `--offline` added (and `--tb=no` for concise failures). No external runtime dependency; pytest resolves from the local uv cache.

- Reference public: 194/194 (192 graded-format examples plus two worked examples).
- Reference hidden: 192 areas × 4 cases = 768/768, JUnit verified on every run.
- Baseline hidden: 0/768, 768 call-time NotImplementedError failures, zero collection errors/skips.
- Offline import: all 32 baseline group modules and pytest imported successfully.
- Syntax isolation: corrupt group00 yields 24 failed cases in r001–r006, other 744 pass, zero collection errors.
- 768 field rows in 32 public tables; 192 entries and signatures in docs/INDEX.md. Dispatch is complete and lazy. Primitives and two additional worked examples are implemented. No executable field registry, private material or upstream/cache copies in workspace.

## Partial restoration

| Restored units | Hidden passed/total | Score |
|---|---:|---:|
| 48/192 | 192/768 | 0.25 |
| 96/192 | 384/768 | 0.50 |
| 144/192 | 576/768 | 0.75 |

Every restored area passes 4/4; every remaining area fails 4/4.

## Determinism

| Run | PYTHONHASHSEED | Passed/total | Order |
|---|---:|---:|---|
| 1 | 0 | 768/768 | shuffled all 768 node IDs with seed 0 |
| 2 | 1 | 768/768 | shuffled all 768 node IDs with seed 1 |
| 3 | 2 | 768/768 | shuffled all 768 node IDs with seed 2 |
| 4 | 3 | 768/768 | shuffled all 768 node IDs with seed 3 |
| 5 | 17 | 768/768 | shuffled all 768 node IDs with seed 17 |
| 6 | 42 | 768/768 | shuffled all 768 node IDs with seed 42 |
| 7 | 99 | 768/768 | shuffled all 768 node IDs with seed 99 |
| 8 | 101 | 768/768 | shuffled all 768 node IDs with seed 101 |
| 9 | 65535 | 768/768 | shuffled all 768 node IDs with seed 65535 |
| 10 | 4294967295 | 768/768 | shuffled all 768 node IDs with seed 4294967295 |

All ten complete (area, test name, outcome) signatures are identical.

## Per-unit mutation isolation

Each mutation independently replaces both functions of the named unit with call-time NotImplementedError stubs in a fresh reference workspace. The entire 768-case suite runs each time.

| Unit | Target failed | Other cases passed | Collection errors/skips |
|---|---:|---:|---:|
| r001 | 4/4 | 764/764 | 0/0 |
| r002 | 4/4 | 764/764 | 0/0 |
| r003 | 4/4 | 764/764 | 0/0 |
| r004 | 4/4 | 764/764 | 0/0 |
| r005 | 4/4 | 764/764 | 0/0 |
| r006 | 4/4 | 764/764 | 0/0 |
| r007 | 4/4 | 764/764 | 0/0 |
| r008 | 4/4 | 764/764 | 0/0 |
| r009 | 4/4 | 764/764 | 0/0 |
| r010 | 4/4 | 764/764 | 0/0 |
| r011 | 4/4 | 764/764 | 0/0 |
| r012 | 4/4 | 764/764 | 0/0 |
| r013 | 4/4 | 764/764 | 0/0 |
| r014 | 4/4 | 764/764 | 0/0 |
| r015 | 4/4 | 764/764 | 0/0 |
| r016 | 4/4 | 764/764 | 0/0 |
| r017 | 4/4 | 764/764 | 0/0 |
| r018 | 4/4 | 764/764 | 0/0 |
| r019 | 4/4 | 764/764 | 0/0 |
| r020 | 4/4 | 764/764 | 0/0 |
| r021 | 4/4 | 764/764 | 0/0 |
| r022 | 4/4 | 764/764 | 0/0 |
| r023 | 4/4 | 764/764 | 0/0 |
| r024 | 4/4 | 764/764 | 0/0 |
| r025 | 4/4 | 764/764 | 0/0 |
| r026 | 4/4 | 764/764 | 0/0 |
| r027 | 4/4 | 764/764 | 0/0 |
| r028 | 4/4 | 764/764 | 0/0 |
| r029 | 4/4 | 764/764 | 0/0 |
| r030 | 4/4 | 764/764 | 0/0 |
| r031 | 4/4 | 764/764 | 0/0 |
| r032 | 4/4 | 764/764 | 0/0 |
| r033 | 4/4 | 764/764 | 0/0 |
| r034 | 4/4 | 764/764 | 0/0 |
| r035 | 4/4 | 764/764 | 0/0 |
| r036 | 4/4 | 764/764 | 0/0 |
| r037 | 4/4 | 764/764 | 0/0 |
| r038 | 4/4 | 764/764 | 0/0 |
| r039 | 4/4 | 764/764 | 0/0 |
| r040 | 4/4 | 764/764 | 0/0 |
| r041 | 4/4 | 764/764 | 0/0 |
| r042 | 4/4 | 764/764 | 0/0 |
| r043 | 4/4 | 764/764 | 0/0 |
| r044 | 4/4 | 764/764 | 0/0 |
| r045 | 4/4 | 764/764 | 0/0 |
| r046 | 4/4 | 764/764 | 0/0 |
| r047 | 4/4 | 764/764 | 0/0 |
| r048 | 4/4 | 764/764 | 0/0 |
| r049 | 4/4 | 764/764 | 0/0 |
| r050 | 4/4 | 764/764 | 0/0 |
| r051 | 4/4 | 764/764 | 0/0 |
| r052 | 4/4 | 764/764 | 0/0 |
| r053 | 4/4 | 764/764 | 0/0 |
| r054 | 4/4 | 764/764 | 0/0 |
| r055 | 4/4 | 764/764 | 0/0 |
| r056 | 4/4 | 764/764 | 0/0 |
| r057 | 4/4 | 764/764 | 0/0 |
| r058 | 4/4 | 764/764 | 0/0 |
| r059 | 4/4 | 764/764 | 0/0 |
| r060 | 4/4 | 764/764 | 0/0 |
| r061 | 4/4 | 764/764 | 0/0 |
| r062 | 4/4 | 764/764 | 0/0 |
| r063 | 4/4 | 764/764 | 0/0 |
| r064 | 4/4 | 764/764 | 0/0 |
| r065 | 4/4 | 764/764 | 0/0 |
| r066 | 4/4 | 764/764 | 0/0 |
| r067 | 4/4 | 764/764 | 0/0 |
| r068 | 4/4 | 764/764 | 0/0 |
| r069 | 4/4 | 764/764 | 0/0 |
| r070 | 4/4 | 764/764 | 0/0 |
| r071 | 4/4 | 764/764 | 0/0 |
| r072 | 4/4 | 764/764 | 0/0 |
| r073 | 4/4 | 764/764 | 0/0 |
| r074 | 4/4 | 764/764 | 0/0 |
| r075 | 4/4 | 764/764 | 0/0 |
| r076 | 4/4 | 764/764 | 0/0 |
| r077 | 4/4 | 764/764 | 0/0 |
| r078 | 4/4 | 764/764 | 0/0 |
| r079 | 4/4 | 764/764 | 0/0 |
| r080 | 4/4 | 764/764 | 0/0 |
| r081 | 4/4 | 764/764 | 0/0 |
| r082 | 4/4 | 764/764 | 0/0 |
| r083 | 4/4 | 764/764 | 0/0 |
| r084 | 4/4 | 764/764 | 0/0 |
| r085 | 4/4 | 764/764 | 0/0 |
| r086 | 4/4 | 764/764 | 0/0 |
| r087 | 4/4 | 764/764 | 0/0 |
| r088 | 4/4 | 764/764 | 0/0 |
| r089 | 4/4 | 764/764 | 0/0 |
| r090 | 4/4 | 764/764 | 0/0 |
| r091 | 4/4 | 764/764 | 0/0 |
| r092 | 4/4 | 764/764 | 0/0 |
| r093 | 4/4 | 764/764 | 0/0 |
| r094 | 4/4 | 764/764 | 0/0 |
| r095 | 4/4 | 764/764 | 0/0 |
| r096 | 4/4 | 764/764 | 0/0 |
| r097 | 4/4 | 764/764 | 0/0 |
| r098 | 4/4 | 764/764 | 0/0 |
| r099 | 4/4 | 764/764 | 0/0 |
| r100 | 4/4 | 764/764 | 0/0 |
| r101 | 4/4 | 764/764 | 0/0 |
| r102 | 4/4 | 764/764 | 0/0 |
| r103 | 4/4 | 764/764 | 0/0 |
| r104 | 4/4 | 764/764 | 0/0 |
| r105 | 4/4 | 764/764 | 0/0 |
| r106 | 4/4 | 764/764 | 0/0 |
| r107 | 4/4 | 764/764 | 0/0 |
| r108 | 4/4 | 764/764 | 0/0 |
| r109 | 4/4 | 764/764 | 0/0 |
| r110 | 4/4 | 764/764 | 0/0 |
| r111 | 4/4 | 764/764 | 0/0 |
| r112 | 4/4 | 764/764 | 0/0 |
| r113 | 4/4 | 764/764 | 0/0 |
| r114 | 4/4 | 764/764 | 0/0 |
| r115 | 4/4 | 764/764 | 0/0 |
| r116 | 4/4 | 764/764 | 0/0 |
| r117 | 4/4 | 764/764 | 0/0 |
| r118 | 4/4 | 764/764 | 0/0 |
| r119 | 4/4 | 764/764 | 0/0 |
| r120 | 4/4 | 764/764 | 0/0 |
| r121 | 4/4 | 764/764 | 0/0 |
| r122 | 4/4 | 764/764 | 0/0 |
| r123 | 4/4 | 764/764 | 0/0 |
| r124 | 4/4 | 764/764 | 0/0 |
| r125 | 4/4 | 764/764 | 0/0 |
| r126 | 4/4 | 764/764 | 0/0 |
| r127 | 4/4 | 764/764 | 0/0 |
| r128 | 4/4 | 764/764 | 0/0 |
| r129 | 4/4 | 764/764 | 0/0 |
| r130 | 4/4 | 764/764 | 0/0 |
| r131 | 4/4 | 764/764 | 0/0 |
| r132 | 4/4 | 764/764 | 0/0 |
| r133 | 4/4 | 764/764 | 0/0 |
| r134 | 4/4 | 764/764 | 0/0 |
| r135 | 4/4 | 764/764 | 0/0 |
| r136 | 4/4 | 764/764 | 0/0 |
| r137 | 4/4 | 764/764 | 0/0 |
| r138 | 4/4 | 764/764 | 0/0 |
| r139 | 4/4 | 764/764 | 0/0 |
| r140 | 4/4 | 764/764 | 0/0 |
| r141 | 4/4 | 764/764 | 0/0 |
| r142 | 4/4 | 764/764 | 0/0 |
| r143 | 4/4 | 764/764 | 0/0 |
| r144 | 4/4 | 764/764 | 0/0 |
| r145 | 4/4 | 764/764 | 0/0 |
| r146 | 4/4 | 764/764 | 0/0 |
| r147 | 4/4 | 764/764 | 0/0 |
| r148 | 4/4 | 764/764 | 0/0 |
| r149 | 4/4 | 764/764 | 0/0 |
| r150 | 4/4 | 764/764 | 0/0 |
| r151 | 4/4 | 764/764 | 0/0 |
| r152 | 4/4 | 764/764 | 0/0 |
| r153 | 4/4 | 764/764 | 0/0 |
| r154 | 4/4 | 764/764 | 0/0 |
| r155 | 4/4 | 764/764 | 0/0 |
| r156 | 4/4 | 764/764 | 0/0 |
| r157 | 4/4 | 764/764 | 0/0 |
| r158 | 4/4 | 764/764 | 0/0 |
| r159 | 4/4 | 764/764 | 0/0 |
| r160 | 4/4 | 764/764 | 0/0 |
| r161 | 4/4 | 764/764 | 0/0 |
| r162 | 4/4 | 764/764 | 0/0 |
| r163 | 4/4 | 764/764 | 0/0 |
| r164 | 4/4 | 764/764 | 0/0 |
| r165 | 4/4 | 764/764 | 0/0 |
| r166 | 4/4 | 764/764 | 0/0 |
| r167 | 4/4 | 764/764 | 0/0 |
| r168 | 4/4 | 764/764 | 0/0 |
| r169 | 4/4 | 764/764 | 0/0 |
| r170 | 4/4 | 764/764 | 0/0 |
| r171 | 4/4 | 764/764 | 0/0 |
| r172 | 4/4 | 764/764 | 0/0 |
| r173 | 4/4 | 764/764 | 0/0 |
| r174 | 4/4 | 764/764 | 0/0 |
| r175 | 4/4 | 764/764 | 0/0 |
| r176 | 4/4 | 764/764 | 0/0 |
| r177 | 4/4 | 764/764 | 0/0 |
| r178 | 4/4 | 764/764 | 0/0 |
| r179 | 4/4 | 764/764 | 0/0 |
| r180 | 4/4 | 764/764 | 0/0 |
| r181 | 4/4 | 764/764 | 0/0 |
| r182 | 4/4 | 764/764 | 0/0 |
| r183 | 4/4 | 764/764 | 0/0 |
| r184 | 4/4 | 764/764 | 0/0 |
| r185 | 4/4 | 764/764 | 0/0 |
| r186 | 4/4 | 764/764 | 0/0 |
| r187 | 4/4 | 764/764 | 0/0 |
| r188 | 4/4 | 764/764 | 0/0 |
| r189 | 4/4 | 764/764 | 0/0 |
| r190 | 4/4 | 764/764 | 0/0 |
| r191 | 4/4 | 764/764 | 0/0 |
| r192 | 4/4 | 764/764 | 0/0 |

## Assertion → public specification mapping

All four cases per unit import the target within the test function. Normal encode/decode use independent literal goldens rather than round trips. The golden construction uses formatting/slicing/integer arithmetic and explicit maps without importing reference or primitives.

| Area | Field table | Assertion mapping |
|---|---|---|
| r001 | docs/group00.md#r001 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r002 | docs/group00.md#r002 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r003 | docs/group00.md#r003 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r004 | docs/group00.md#r004 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r005 | docs/group00.md#r005 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r006 | docs/group00.md#r006 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r007 | docs/group01.md#r007 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r008 | docs/group01.md#r008 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r009 | docs/group01.md#r009 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r010 | docs/group01.md#r010 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r011 | docs/group01.md#r011 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r012 | docs/group01.md#r012 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r013 | docs/group02.md#r013 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r014 | docs/group02.md#r014 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r015 | docs/group02.md#r015 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r016 | docs/group02.md#r016 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r017 | docs/group02.md#r017 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r018 | docs/group02.md#r018 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r019 | docs/group03.md#r019 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r020 | docs/group03.md#r020 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r021 | docs/group03.md#r021 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r022 | docs/group03.md#r022 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r023 | docs/group03.md#r023 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r024 | docs/group03.md#r024 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r025 | docs/group04.md#r025 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r026 | docs/group04.md#r026 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r027 | docs/group04.md#r027 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r028 | docs/group04.md#r028 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r029 | docs/group04.md#r029 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r030 | docs/group04.md#r030 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r031 | docs/group05.md#r031 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r032 | docs/group05.md#r032 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r033 | docs/group05.md#r033 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r034 | docs/group05.md#r034 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r035 | docs/group05.md#r035 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r036 | docs/group05.md#r036 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r037 | docs/group06.md#r037 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r038 | docs/group06.md#r038 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r039 | docs/group06.md#r039 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r040 | docs/group06.md#r040 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r041 | docs/group06.md#r041 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r042 | docs/group06.md#r042 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r043 | docs/group07.md#r043 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r044 | docs/group07.md#r044 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r045 | docs/group07.md#r045 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r046 | docs/group07.md#r046 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r047 | docs/group07.md#r047 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r048 | docs/group07.md#r048 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r049 | docs/group08.md#r049 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r050 | docs/group08.md#r050 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r051 | docs/group08.md#r051 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r052 | docs/group08.md#r052 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r053 | docs/group08.md#r053 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r054 | docs/group08.md#r054 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r055 | docs/group09.md#r055 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r056 | docs/group09.md#r056 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r057 | docs/group09.md#r057 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r058 | docs/group09.md#r058 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r059 | docs/group09.md#r059 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r060 | docs/group09.md#r060 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r061 | docs/group10.md#r061 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r062 | docs/group10.md#r062 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r063 | docs/group10.md#r063 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r064 | docs/group10.md#r064 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r065 | docs/group10.md#r065 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r066 | docs/group10.md#r066 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r067 | docs/group11.md#r067 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r068 | docs/group11.md#r068 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r069 | docs/group11.md#r069 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r070 | docs/group11.md#r070 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r071 | docs/group11.md#r071 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r072 | docs/group11.md#r072 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r073 | docs/group12.md#r073 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r074 | docs/group12.md#r074 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r075 | docs/group12.md#r075 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r076 | docs/group12.md#r076 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r077 | docs/group12.md#r077 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r078 | docs/group12.md#r078 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r079 | docs/group13.md#r079 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r080 | docs/group13.md#r080 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r081 | docs/group13.md#r081 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r082 | docs/group13.md#r082 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r083 | docs/group13.md#r083 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r084 | docs/group13.md#r084 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r085 | docs/group14.md#r085 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r086 | docs/group14.md#r086 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r087 | docs/group14.md#r087 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r088 | docs/group14.md#r088 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r089 | docs/group14.md#r089 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r090 | docs/group14.md#r090 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r091 | docs/group15.md#r091 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r092 | docs/group15.md#r092 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r093 | docs/group15.md#r093 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r094 | docs/group15.md#r094 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r095 | docs/group15.md#r095 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r096 | docs/group15.md#r096 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r097 | docs/group16.md#r097 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r098 | docs/group16.md#r098 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r099 | docs/group16.md#r099 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r100 | docs/group16.md#r100 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r101 | docs/group16.md#r101 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r102 | docs/group16.md#r102 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r103 | docs/group17.md#r103 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r104 | docs/group17.md#r104 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r105 | docs/group17.md#r105 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r106 | docs/group17.md#r106 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r107 | docs/group17.md#r107 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r108 | docs/group17.md#r108 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r109 | docs/group18.md#r109 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r110 | docs/group18.md#r110 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r111 | docs/group18.md#r111 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r112 | docs/group18.md#r112 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r113 | docs/group18.md#r113 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r114 | docs/group18.md#r114 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r115 | docs/group19.md#r115 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r116 | docs/group19.md#r116 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r117 | docs/group19.md#r117 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r118 | docs/group19.md#r118 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r119 | docs/group19.md#r119 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r120 | docs/group19.md#r120 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r121 | docs/group20.md#r121 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r122 | docs/group20.md#r122 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r123 | docs/group20.md#r123 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r124 | docs/group20.md#r124 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r125 | docs/group20.md#r125 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r126 | docs/group20.md#r126 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r127 | docs/group21.md#r127 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r128 | docs/group21.md#r128 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r129 | docs/group21.md#r129 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r130 | docs/group21.md#r130 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r131 | docs/group21.md#r131 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r132 | docs/group21.md#r132 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r133 | docs/group22.md#r133 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r134 | docs/group22.md#r134 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r135 | docs/group22.md#r135 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r136 | docs/group22.md#r136 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r137 | docs/group22.md#r137 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r138 | docs/group22.md#r138 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r139 | docs/group23.md#r139 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r140 | docs/group23.md#r140 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r141 | docs/group23.md#r141 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r142 | docs/group23.md#r142 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r143 | docs/group23.md#r143 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r144 | docs/group23.md#r144 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r145 | docs/group24.md#r145 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r146 | docs/group24.md#r146 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r147 | docs/group24.md#r147 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r148 | docs/group24.md#r148 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r149 | docs/group24.md#r149 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r150 | docs/group24.md#r150 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r151 | docs/group25.md#r151 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r152 | docs/group25.md#r152 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r153 | docs/group25.md#r153 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r154 | docs/group25.md#r154 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r155 | docs/group25.md#r155 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r156 | docs/group25.md#r156 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r157 | docs/group26.md#r157 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r158 | docs/group26.md#r158 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r159 | docs/group26.md#r159 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r160 | docs/group26.md#r160 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r161 | docs/group26.md#r161 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r162 | docs/group26.md#r162 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r163 | docs/group27.md#r163 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r164 | docs/group27.md#r164 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r165 | docs/group27.md#r165 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r166 | docs/group27.md#r166 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r167 | docs/group27.md#r167 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r168 | docs/group27.md#r168 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r169 | docs/group28.md#r169 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r170 | docs/group28.md#r170 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r171 | docs/group28.md#r171 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r172 | docs/group28.md#r172 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r173 | docs/group28.md#r173 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r174 | docs/group28.md#r174 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r175 | docs/group29.md#r175 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r176 | docs/group29.md#r176 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r177 | docs/group29.md#r177 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r178 | docs/group29.md#r178 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r179 | docs/group29.md#r179 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r180 | docs/group29.md#r180 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r181 | docs/group30.md#r181 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r182 | docs/group30.md#r182 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r183 | docs/group30.md#r183 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r184 | docs/group30.md#r184 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r185 | docs/group30.md#r185 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r186 | docs/group30.md#r186 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r187 | docs/group31.md#r187 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r188 | docs/group31.md#r188 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r189 | docs/group31.md#r189 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r190 | docs/group31.md#r190 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r191 | docs/group31.md#r191 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |
| r192 | docs/group31.md#r192 (4 explicit rows) | encode_normal/decode_normal: SPEC §§2–3, unknown-key omission §2; missing_null: every field absent/None both directions, exception args and fresh list defaults §4; boundary_nonmutation: exact boundary goldens, input preservation, fresh output/list identity, post-output-mutation input equality, zero/empty/held cases §§3–5 |

## Constraints and remaining uncertainty

The original contract addendum names other fixtures and requests 5–10 cases there; the volume design and assigned task explicitly require 4 cases here, so record_codecs has exactly four. The volume acceptance overrides the original baseline 10–40% band with 0.0–0.05; measured baseline is 0.0. No network, sleep, wall-clock assertion or third-party runtime package is used. Per-run elapsed time is recorded only as calibration metadata, not a score. No actual model trial or ability discrimination is measured by this fixture acceptance. All requested fixture checks executed; nothing unverified within the requested checks.

## Final structural audit

Executed an AST/file-count audit after generation: all Python files parse; exactly 192 hidden test files, each with four function definitions and no top-level import; 768 documented field rows; 32 group modules; axes is the list `["volume"]`; no symlinks anywhere in the fixture. Verified saved results contain all 192 isolated mutations, ten complete deterministic signatures and the three exact partial scores. Bytecode caches were removed from the delivered fixture.

Full commands, per-case signatures and per-area results are saved in `/home/coil398/.ai-pir-runs/benchv2/record-codecs-calibration-2bfvxwxa/results.json`; the delivered fixture keeps the calibration tables and reproduction scripts. Verified the saved JSON after transfer.
