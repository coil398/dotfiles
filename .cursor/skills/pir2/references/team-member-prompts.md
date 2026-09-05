# PIR² async — Cursor の実行契約

このファイルは旧いチーム形式のテンプレートを実行するためのものではありません。Cursor では専用チームの lifecycle やメンバー間直接通信を使用せず、`/pir2async` は `${CURSOR_SKILLS_DIR}/pir2async/SKILL.md` を Read して、同じ引数で `/pir2` の通常 Task ワークフローへ明示的に縮退します。

## 現行契約

- 子担当は通常の `Task(subagent_type=...)` のみ。モデルは省略または `inherit` とし、deepthink / deepplan の Fable 例外だけはそれぞれの Skill の契約に従う。
- 実装・レビュー・テストの起動、順序、ループ、ユーザー確認、最終受入は `${CURSOR_SKILLS_DIR}/pir2/SKILL.md` のメインが所有する。
- reviewer / tester は実際に起動した担当だけを扱う。固定人数、未起動担当の VERDICT、未生成 report / plan の必須化はしない。
- report は親が保存を決めた実在 path にだけ保存する。保存不要ならチャット要約を返す。
- handoff / experimental は親が渡した実在 path だけを扱い、存在しない path を推測・作成しない。
- 実行結果を別形式へ変換したり、存在しない担当・artifact・VERDICTを補ったりしない。

詳細な実行手順は `${CURSOR_SKILLS_DIR}/pir2/SKILL.md` と、その実行時に解決された references を SSOT とする。このファイルへ旧 runtime の lifecycle、メンバー向けテンプレート、固定 report パスを戻してはならない。
