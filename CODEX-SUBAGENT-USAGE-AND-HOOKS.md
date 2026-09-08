# Subagent使用量の調査とCodex native sync hookの修正

確認日: 2026-09-08（日本時間）。修正の起点は `27b94a4d36101b4d57612f5f9c2318820976412b`。
本書は調査結果と今回の限定修正の記録であり、既存の[運用設計](AI-WORKFLOW-SPEC.md)やモデル選択方針を変更しない。

## 調査結果

OpenAIは、各subagentが独立してモデルとツールを使うため、同等の単一agent実行よりトークンが増えると説明している。Cursorも各子の消費が独立しており、五体並列では一体のおよそ五倍という目安を示す。固定の倍率をすべてのタスクへ適用する意味ではない。[S1][S2]

Anthropicの研究システムでは通常のagentがチャットの約4倍、multi-agentがチャットの約15倍という観測が公表されている。15倍の比較対象は単一agentではなくチャットであり、Codexの請求倍率ではない。[S3]

総量は親の実行・配分・統合と、各子の入力・推論・出力の合計になる。子ごとの共通指示や対象コードの読込、重複調査、長い結果、親の再確認は追加の処理である。推論トークンはAPIでは出力として課金され、キャッシュの読取も無料ではない。GPT-5.6以降のAPIにはキャッシュ書込料金もあるため、入力総量だけで費用を判断しない。[S4][S5]

APIの料金、Cursorの利用額、ChatGPTプランの使用枠は同じ指標ではない。OpenAIはプラン消費が仕事の規模・モデル・実行場所・セッション長で変わると説明している。実際の利用明細や実行ログなしに、今回の消費原因・削減率は確定できない。[S6]

### 利用者による障害報告（この環境では未再現）

- OpenAI Codex #37299: Desktopで短いwait/statusを繰り返し、長い文脈を再処理することと、完了した子がrunningのまま残ることを報告している。利用者の測定・推定であり、全版への影響や請求計算が公式に確認されたことを意味しない。[R1]
- OpenAI Codex #39894: CLI 0.149.0で親を通常モードに戻した後も子がpriorityとして記録された、と報告している。利用者はFast課金の確認を求めており、この報告だけで現在の全利用者の課金障害とは断定できない。[R2]

この二つは、正常な並列処理の費用と分けて調べる候補である。ユーザーのセッション・請求・認証データは今回取得していない。

## 運用上の推奨（設定は未変更）

小変更は親が直接進める。独立作業や独立評価が必要な場合だけ子を使い、五観点と五体を同義にしない。独立性が明示された依頼はそのまま維持する。

子には必要な対象・専門資料・完了条件を渡し、不要な全履歴コピーと同じコードの重複探索を避ける。完了通知や公開された長待機の仕組みがある場合はそれを使い、変化のない状態確認だけで短いモデルターンを繰り返さない。短い返却でも根拠・未確認範囲は残す。

単純な検索まで最大推論量を必要条件にせず、既存方針の範囲でモデルと推論量を選ぶ。モデル・Fast/standard・APIキャッシュ設定の受理は実際のruntimeで確認する。APIのパラメータをCodexのconfigへ推測で追加しない。

使用量を調べる際は、親子別の実モデル・推論量・service tier、実行ターン数、未キャッシュ入力・キャッシュ読取/書込・出力/推論、待機確認の回数を見る。累計カウンタを毎行合算したり、forkで再出力された過去イベントを新規消費として二重計上しない。観測できない値は未確認のまま扱う。

## フックの原因と修正

旧 `etc/sync-codex.sh` はCodexの `PostToolUse` に生成処理自身を登録していた。`Edit|Write` はnativeの `apply_patch` にも一致する。Claude用の `.claude/lib/sync-codex-hook.sh` を限定しても、この別経路には反映されなかった。[S7]

修正後は以下の経路となる。

```text
Codex apply_patch
  -> etc/sync-codex-hook.py
  -> tool_input.commandの変更パスをevent.cwd基準で解決
  -> Codex生成元・Skill入口の変更がある場合だけetc/sync-codex.sh
```

判定対象はhelper内の `SOURCE_FILES` と共有/nativeの直下Skill入口である。通常のアプリ編集、他repoのAGENTS、直接読まれる専門reference、生成済みconfigの変更では再生成しない。追加・削除・移動・複数ファイルを扱い、一イベントで最大一回実行する。patch本文をshellとして実行しない。

無関係な編集と同期成功は無出力。失敗時だけ短いPostToolUse追加情報を返し、生成ログや認証情報をモデル文脈へ流さない。元の編集を取り消す出力や承認の自動許可は返さない。既存のhook trustを保全し、新しいtrusted hashは作らない。

このhookはモデルを直接呼ばない。また公式ではPostToolUseの通常stdoutは無視される。従って旧hookのローカル処理増加は確認できても、大量トークン消費の主因や今回の課金削減率まで証明したことにはならない。[S7]

## 実施したテスト

`etc/test-codex-native-sync-hook.py` は本物の生成scriptを隔離HOMEで実行し、生成TOMLから実際のhook commandを取り出して試験する。その後、隔離した生成処理だけを呼出回数の記録用に置換する。旧generatorでは無関係な編集でも一回起動し、期待0回の試験が失敗することを再現した。

修正後は16テストが成功した。対象外編集、他repo、event.cwd、絶対パス、複数変更、Skill追加/削除/移動、生成物、入力本文中の偽header、root外パス、symlink、未知tool、不正入力、失敗時の返却、trust保全を含む。`bash -n etc/sync-codex.sh`も成功した。

```sh
uv run --python 3.13 python etc/test-codex-native-sync-hook.py
```

テスト環境はLinuxとPython 3.13。Codexへの推論依頼、外部ネットワーク、利用者HOMEの変更は行っていない。Mac/Windows実機、ライブCodexイベント、実際の課金額は未検証。従来の `test-sync-hooks.sh` はClaude経路を試験するもので、このnative試験とは区別する。

## 利用端末への反映

更新済みdotfilesのローカルcheckoutで、既存の生成・配布を一度実行する。

```sh
bash etc/link.sh --codex-cursor-only
```

`.codex/config.toml` は端末固有の生成物であり、この変更に個人の絶対パス入りconfigを含めない。生成後のhook commandが `python3 .../etc/sync-codex-hook.py` であることを確認する。変更したhookの信頼確認が表示された場合は内容を確認して通常の手順で承認する。稼働中のセッションだけで更新済みと判断せず、新規セッションで確認する。

## 出典

- [S1: OpenAI Subagents](https://developers.openai.com/codex/subagents)
- [S2: Cursor Subagents — Performance and cost](https://cursor.com/docs/subagents)
- [S3: Anthropic multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [S4: OpenAI Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
- [S5: OpenAI Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [S6: Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- [S7: OpenAI Hooks — PostToolUse](https://developers.openai.com/codex/hooks)
- [R1: Codex #37299、利用者による待機・状態確認の報告](https://github.com/openai/codex/issues/37299)
- [R2: Codex #39894、利用者による子のpriority状態の報告](https://github.com/openai/codex/issues/39894)
