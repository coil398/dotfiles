# 明示 CLI runner 契約

この文書は、native collaboration ではなく `.codex/skills/worker-delegation/scripts/run-worker.sh` を明示的に選択した job の実行契約です。runner は actor を選択せず、親Astraが決めた actor と effort を固定して実行します。runner の終了コードや worker の自己申告だけで受入を確定しません。

## 呼び出しと actor

通常の実装は native collaboration で行い、次のような場合だけ runner を使います。

- 明示的な `codex exec` と、raw report/provenance artifact の保存が必要な場合
- 実行中の cwd、`.codex`、出力先、変更集合を物理境界付きで記録する必要がある場合
- 呼び出し元が runner の no-replace artifact と決定論的な変更集合を受入証拠にする場合

対応は次のとおりです。

| 親が選ぶ担当 | runner の指定 | 実行モデル / effort |
| --- | --- | --- |
| `worker` | `--actor luna --effort max` | `gpt-5.6-luna` / `max` |
| `expert` | `--actor sol --effort high` | `gpt-5.6-sol` / `high` |
| `expert_max` | `--actor sol --effort max` | `gpt-5.6-sol` / `max` |
| workload-specific Terra exception | `--actor terra --effort high|max` | `gpt-5.6-terra` / 指定値 |

runner は選択した actor/effort/model を変更せず、自動 fallback、blind retry、自己判断の昇格を行いません。入力不足、要件の曖昧さ、権限・環境・CLIの失敗は能力不足の証拠ではないため、別 actor を起動せず Astra に blocker として返します。難所を事前に把握している場合は、Luna/Terra を先に実行せず `expert` / `expert_max` を直接選べます。

worker prompt は親Astraが既にスコープを決めた作業として扱います。routine の実装詳細は task、リポジトリの規約、既存テストから解決し、routine 詳細が文章にないだけで停止しません。正確性・安全性に関わる決定の欠落、許可範囲外の操作、または権限不足だけを blocker として Astra に返します。

## 実行時間

`run-worker.sh` 自体には実行時間上限を設けません。worker の長い調査・編集・検証を、呼び出し側の短い shell/tool timeout で終了させてはいけません。

- timeout を省略できる基盤では完了まで待つ。
- timeout が必須の基盤では `timeout_ms: 3600000`（1時間）以上を指定し、10分以下の既定値や見積もり時間ぴったりの値を使わない。
- 長時間無出力は失敗とみなさず、wait/resume 機構で同じ process の完了を待つ。
- ユーザーの中止、確定した入力・権限 blocker、または実測した停止以外の理由で中断しない。
- `codex_exit=101` と短い `duration_ms` が同時に記録されたら、能力不足へ昇格する前に外枠 timeout/process termination を調べる。

## source ownership と安全境界

`.codex/` 配下を worker が所有する場合だけ、taskの排他的所有範囲に一致する最も狭い prefix を `--mutable-path <repo-relative-path>` として繰り返し指定できます。これは tree identity の除外対象を限定する source-ownership metadata であり、`.codex/` への書き込み権限や filesystem permission の昇格ではありません。prefix は正規化済みで `.codex/` より下にあり、重複・nested 宣言は整理されます。UID、group/world writable、symlink、`.git`、同一 Git root の検査は mutable prefix にも適用されます。指定しない場合は `.codex/` 全体を identity-pinned として扱います。

runner source 自体（`run-worker.sh` または同じ runner source）を変更する job は他の runner job と並列にしません。起動前に current runner を current UID 所有・`0700` の private temporary directory へ複製し、owner-write を除いた immutable execution copy を固定して、その copy から実行します。

runner が worker prompt に注入する境界も維持します。既存の変更や他担当の変更を破棄する操作（`reset`、`checkout`、`restore`、`clean`、`stash` を含む）、commit/push、別 agent・worker・reviewer・tester の起動、所有範囲外への変更を禁止します。routine の実装詳細は task、リポジトリ規約、既存テストから解決させ、正確性・安全性に関わる未決定事項、許可範囲外の操作、権限不足だけを Astra へ blocker として返します。

既存 runner の次の境界を維持します。

- cwd は物理的な Git top-level と一致し、cwd直下の `.codex` は実体ある非symlinkで同じ root 内にある。
- `.codex` descendant の symlink は、同じ Git root 内の current UID 所有・group/world non-writable な実体へ1段だけ解決し、外部、broken、nested、`.git` 向けを拒否する。
- portable inventory は Perl core の `File::Find`、`Cwd`、`Digest::SHA` を使い、利用不能なら fail-closed する。
- task/requirements は空でなく、requirements は `- R<number>:` 形式を少なくとも1件持つ。
- 出力先は canonical cwd 内または実体ある非symlinkの標準 `$HOME/.ai-pir-runs` artifact root 内だけ。許可 root から output parent までの全 directory component を current UID 所有・non-writable・identity固定として検査する。
- `pre-codex`、`post-codex`、`pre-publish` で root、`.codex` descendant、output chain、raw report slot、provenance slot を再検証する。raw report と sidecar は同一 filesystem の no-replace link で公開し、既存 slot や symlink を上書きしない。
- Codex には JSON mode、workspace-write、canonical `-C`/`--add-dir`、stdin prompt を渡し、`--disable hooks` を明示する。`danger-full-access`、sandbox bypass、権限調整の `chmod` は使わない。
- runner と runner が作る scratch/artifact は `umask 077` を初期値とし、cleanup は identity を確認できる単一の task-local temp に限定します。広い glob や未解決の環境変数で既存データを削除しません。

この hardening は設定ミス、静的 symlink、他 UID/信頼できない group の書込み、検出可能な偶発的競合を対象とします。malicious same-UID host process または完全に信頼できない same-UID worker に対する完全な TOCTOU 防止は主張しません。Codex CLI は path string しか受け取れず、runner は directory/file descriptor capability を渡せないため、`openat` や atomic open を追加しても path 境界を完全には解決できません。完全な same-UID 分離が必要なら別 UID、OS sandbox、mount isolation、または fd-capability を持つ CLI を使います。

PowerShell から Git for Windows の runner に絶対パスを渡す場合は、`C:\Users\...`、`C:/Users/...`、Git Bash 内部の `/c/Users/...` を同一の正規パスへ正規化します。この経路に WSL は含めません。drive-relative（`C:foo`）、UNC/double-slash、`.`/`..` を含む曖昧な表記は拒否します。cwd/output の symlink 検査は候補の物理 leaf から許可 root まで行い、許可 root より上位の ancestor alias だけを許可します。

## 限定 symlink recovery

runner の fail-closed は維持します。caller が回復できるのは、初回拒否が allowlist の唯一の外部 symlink `.codex/skills/uniskill -> ../../.claude/skills/uniskill` で、cwd や `.codex` 自身は拒否されておらず、task/requirements/所有範囲から worker がそのリンクを必要としない場合だけです。

1. 初回 runner の stderr/exit を保存し、exact path/link text を `readlink`/`realpath`/`lstat`（device/inode、owner、mode）と `git status`、source parent の identity で照合する。
2. 条件を満たす場合だけ、同一 filesystem 上の current UID 所有・`0700`・非symlinkの task-local temp へ exact link entry を `rename` で退避する。target、source parent、親、allowlist の別 slot は動かさない。
3. 同じ task、requirements、actor、effort、その他入力で同じ runner を最大1回だけ再実行する。runner の緩和、別 actor/effort、別 runner、直接 `codex exec`、sandbox bypass は禁止する。
4. 成功・失敗・起動不能・中断を問わず finally で、元 slot が空のときだけ元の link text を同一 filesystem の `rename` で復元する。復元後の `readlink`/`realpath`/`lstat`/`git status`（source parent を含む）を baseline と照合し、占有・置換・消失・identity不一致・復元不能は上書きせず blocker とする。

別 symlink、broken/nested link、複数または曖昧な拒否、cwd/.codex の拒否は recovery 対象ではありません。

## report と実測 identity

runner は raw worker report を未信頼入力として検証します。`ACTOR`、`ACTUAL_MODEL`、`ACTUAL_EFFORT` は選択値との一致を検査するための自己申告であり、実行 identity の証明ではありません。runner-owned provenance sidecar の actor/model/effort、終了時刻、exit、validation status を canonicalization と監査の authoritative source とします。実際のモデル・effort提供やsession記録が確認できないとき、それを確認済みとして補いません。

raw report は canonical 8 fields（`ACTOR`、`ACTUAL_MODEL`、`ACTUAL_EFFORT`、`STATUS`、`CHANGED_FILES`、`OBSERVED_RESULTS`、`BLOCKERS`、`ESCALATION_REASON`）を一意に持ち、actor/model/effort は runner 選択値と一致し、status は `completed|blocked|failed` のいずれかでなければ公開されません。sidecar は Codex 失敗や raw validation 失敗でも記録します。

決定論的 pre/post/CLAIMED gate と `record-observation.sh` は、runnerを選び、その artifact・モデル・effort・変更集合を証拠として残す必要がある job にだけ適用します。native collaboration、Astraの直接実装、単純な小変更では canonical report、8 fixture、meta gate、観測台帳を要求しません。適用時のプロトコルは `deterministic-completion-check.md` を、台帳 schema は `.codex/skills/pir2/references/worker-observability.md` を参照します。

台帳へ actor transition を記録する場合、非昇格は `none→none`、昇格は親Astraが実測理由と十分な入力を添えて `luna→terra`、`luna→sol`、または `terra→sol` を明示します。Solを選ぶための Terra 前置きはなく、runner は transition を自動生成・補正しません。

runner の安全境界を変更した場合は、`tests/test_mutable_paths.sh` など同ディレクトリの境界テストを実行します。runnerを変更していない通常 job で8 fixtureを反復実行する必要はありません。
