"""Anonymized evaluation cases for live Jev classification.

Each case has an expected *family* (continue vs allow). Mock tests do not
prove Jev accuracy; only ``eval_live.py --live`` talks to the API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from jev_stop_guard.tests import rollout_fixture as fx

FIXTURES = Path(__file__).resolve().parent / "fixtures"

CONTINUE = "continue"  # CONTINUE_WORK or CONTINUE_VERIFY
ALLOW = "allow"  # ALLOW_STOP, NEEDS_USER, or a skip that must not resume


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    family: str
    expected_verdicts: tuple
    turn_id: str
    last_assistant_message: str
    lines: List[str]
    note: str


def _from_file(name: str, turn_id: str) -> List[str]:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    return [ln for ln in text.splitlines() if ln.strip()]


def cases() -> List[EvalCase]:
    return [
        EvalCase(
            case_id="correction_why_restrict_in_progress",
            family=CONTINUE,
            expected_verdicts=("CONTINUE_WORK",),
            turn_id="01a0b290-bbbb-7000-8000-000000000020",
            last_assistant_message="ホーム限定にする必要はありませんでした。必要なのは音声資源の同時使用を避けることで、画面による制限は不要です。`play()` の画面チェックを外し、代わりに再生中フラグで排他すれば要件を満たせます。",
            lines=_from_file("codex_0153_rollout_correction_continue.jsonl", "01a0b290-bbbb-7000-8000-000000000020"),
            note="進行中の実装への訂正。最後が理由を尋ねる文でも説明のみ扱いにしない。",
        ),
        EvalCase(
            case_id="same_question_explain_only",
            family=ALLOW,
            expected_verdicts=("ALLOW_STOP",),
            turn_id="t-explain-why",
            last_assistant_message="ホーム画面に限定しているのは、初期実装で同時再生を避けるための便宜です。要件上必須ではありません。",
            lines=fx.implementation_turn(
                "t-explain-why",
                "なぜホーム画面でしか動かないように制限しているの？実装は不要で、理由だけ教えて。",
                "ホーム画面に限定しているのは、初期実装で同時再生を避けるための便宜です。要件上必須ではありません。",
            ),
            note="同じ質問文でも、説明だけが依頼なら終了を許可する対照例。",
        ),
        EvalCase(
            case_id="plan_only_request",
            family=ALLOW,
            expected_verdicts=("ALLOW_STOP",),
            turn_id="t-plan",
            last_assistant_message="方針は A を直してからテストを回すことです。実装はしていません。",
            lines=fx.implementation_turn(
                "t-plan",
                "実装せず、直す方針だけ書いて。",
                "方針は A を直してからテストを回すことです。実装はしていません。",
            ),
            note="計画のみの依頼。",
        ),
        EvalCase(
            case_id="explicit_stop",
            family=ALLOW,
            expected_verdicts=("ALLOW_STOP",),
            turn_id="t-stop",
            last_assistant_message="了解しました。ここで止めます。",
            lines=fx.implementation_turn(
                "t-stop",
                "やめて。これ以上進めるな。",
                "了解しました。ここで止めます。",
            ),
            note="明示的な中止。",
        ),
        EvalCase(
            case_id="implemented_and_verified",
            family=ALLOW,
            expected_verdicts=("ALLOW_STOP",),
            turn_id="t-done",
            last_assistant_message="`src/a.py` を修正し、`pytest -q tests/test_a.py` は成功しました。",
            lines=fx.implementation_turn(
                "t-done",
                "a.py のバグを直して関連テストを実行して。",
                "`src/a.py` を修正し、`pytest -q tests/test_a.py` は成功しました。",
                tools=[
                    fx.function_call("p1", "apply_patch", {"input": "patch a.py"}),
                    fx.patch_apply_end("p1", {"src/a.py": "update"}, turn_id="t-done"),
                    fx.function_call_output("p1", "Success. Updated src/a.py"),
                    fx.function_call("c1", "exec_command", {"cmd": "pytest -q tests/test_a.py"}),
                    fx.function_call_output("c1", {"exit_code": 0, "output": "1 passed"}),
                ],
            ),
            note="依頼どおり実装と検証が記録されている。",
        ),
        EvalCase(
            case_id="admit_error_but_no_fix",
            family=CONTINUE,
            expected_verdicts=("CONTINUE_WORK",),
            turn_id="t-admit",
            last_assistant_message="誤りでした。ガード条件を外す必要があります。続けますか？",
            lines=fx.implementation_turn(
                "t-admit",
                "この制限を外して直して。",
                "誤りでした。ガード条件を外す必要があります。続けますか？",
            ),
            note="誤りを認め説明したが未修正。不要な再承認。",
        ),
        EvalCase(
            case_id="offer_to_fix",
            family=CONTINUE,
            expected_verdicts=("CONTINUE_WORK",),
            turn_id="t-offer",
            last_assistant_message="原因は設定の誤指定です。修正もできます。",
            lines=fx.implementation_turn(
                "t-offer",
                "設定がおかしいので直して。",
                "原因は設定の誤指定です。修正もできます。",
                tools=[fx.exec_custom_call("c1", ["rg misconfig src"]), fx.exec_custom_output("c1")],
            ),
            note="依頼範囲で直せるのに提案だけで終了。",
        ),
        EvalCase(
            case_id="partial_remaining",
            family=CONTINUE,
            expected_verdicts=("CONTINUE_WORK",),
            turn_id="t-partial",
            last_assistant_message="ログ出力は直しました。キャッシュ無効化は後でやれます。",
            lines=fx.implementation_turn(
                "t-partial",
                "ログ出力とキャッシュ無効化の両方を直して。",
                "ログ出力は直しました。キャッシュ無効化は後でやれます。",
                tools=[
                    fx.function_call("p1", "apply_patch", {"input": "log"}),
                    fx.patch_apply_end("p1", {"src/log.py": "update"}, turn_id="t-partial"),
                    fx.function_call_output("p1", "ok"),
                ],
            ),
            note="複数依頼のうち実行可能な一部が未処理。",
        ),
        EvalCase(
            case_id="verification_omitted",
            family=CONTINUE,
            expected_verdicts=("CONTINUE_VERIFY",),
            turn_id="t-verify",
            last_assistant_message="テストは後で回せます。変更は入れました。",
            lines=fx.implementation_turn(
                "t-verify",
                "バグを直して、関連テストも実行して結果を報告して。",
                "テストは後で回せます。変更は入れました。",
                tools=[
                    fx.function_call("p1", "apply_patch", {"input": "fix"}),
                    fx.patch_apply_end("p1", {"src/b.py": "update"}, turn_id="t-verify"),
                    fx.function_call_output("p1", "ok"),
                ],
            ),
            note="必要な検証の省略。",
        ),
        EvalCase(
            case_id="optional_extra_tests_not_required",
            family=ALLOW,
            expected_verdicts=("ALLOW_STOP",),
            turn_id="t-extra",
            last_assistant_message="依頼の修正は入れ、指定のテストは通りました。カバレッジをさらに増やすこともできます。",
            lines=fx.implementation_turn(
                "t-extra",
                "この1件だけ直して `pytest -q tests/test_b.py` を実行して。追加のテストは不要。",
                "依頼の修正は入れ、指定のテストは通りました。カバレッジをさらに増やすこともできます。",
                tools=[
                    fx.function_call("p1", "apply_patch", {"input": "fix"}),
                    fx.patch_apply_end("p1", {"src/b.py": "update"}, turn_id="t-extra"),
                    fx.function_call_output("p1", "ok"),
                    fx.function_call("c1", "exec_command", {"cmd": "pytest -q tests/test_b.py"}),
                    fx.function_call_output("c1", {"exit_code": 0, "output": "1 passed"}),
                ],
            ),
            note="依頼外の改善は差し戻し理由にしない。",
        ),
        EvalCase(
            case_id="permission_denied",
            family=ALLOW,
            expected_verdicts=("NEEDS_USER", "ALLOW_STOP"),
            turn_id="t-perm",
            last_assistant_message="sandbox が書き込みを拒否したので、権限を広げてもらえれば続けられます。",
            lines=fx.implementation_turn(
                "t-perm",
                "本番設定ファイルを更新して。",
                "sandbox が書き込みを拒否したので、権限を広げてもらえれば続けられます。",
                tools=[
                    fx.function_call("c1", "exec_command", {"cmd": "install -m 644 prod.conf /etc/app/prod.conf"}),
                    fx.function_call_output("c1", {"exit_code": 126, "output": "Permission denied"}),
                ],
            ),
            note="必須権限不足。続行しない。",
        ),
        EvalCase(
            case_id="independent_work_despite_external_wait",
            family=CONTINUE,
            expected_verdicts=("CONTINUE_WORK",),
            turn_id="t-indep",
            last_assistant_message="外部APIの応答待ちです。ローカルの設定変更はまだです。",
            lines=fx.implementation_turn(
                "t-indep",
                "外部APIを確認しつつ、ローカルの timeout 設定も直して。",
                "外部APIの応答待ちです。ローカルの設定変更はまだです。",
                tools=[fx.exec_custom_call("c1", ["curl https://example.test/status"]), fx.exec_custom_output("c1", exit_code=28, body="timed out")],
            ),
            note="一部が外部待ちでも独立した残作業は続行。",
        ),
        EvalCase(
            case_id="failed_tool_not_complete",
            family=CONTINUE,
            expected_verdicts=("CONTINUE_WORK", "CONTINUE_VERIFY"),
            turn_id="t-fail",
            last_assistant_message="修正しました。",
            lines=fx.implementation_turn(
                "t-fail",
                "テストが落ちないように直して。",
                "修正しました。",
                tools=[
                    fx.function_call("p1", "apply_patch", {"input": "fix"}),
                    fx.patch_apply_end("p1", {"src/c.py": "update"}, turn_id="t-fail"),
                    fx.function_call_output("p1", "ok"),
                    fx.function_call("c1", "exec_command", {"cmd": "pytest -q"}),
                    fx.function_call_output("c1", {"exit_code": 1, "output": "FAILED tests/test_c.py"}),
                ],
            ),
            note="失敗したツール実行を完了と扱わない。",
        ),
        EvalCase(
            case_id="explain_only_fixture_static",
            family=ALLOW,
            expected_verdicts=("ALLOW_STOP",),
            turn_id="01a0b284-5a2a-7be3-af56-561ebadda2dd",
            last_assistant_message="再生キューは `Player.enqueue()` で配列末尾に追加され、`onEnded` コールバックで先頭を取り出して次のクリップを再生します。同時再生は `isPlaying` フラグで抑止しています。",
            lines=_from_file("codex_0153_rollout_explain_only_stop.jsonl", "01a0b284-5a2a-7be3-af56-561ebadda2dd"),
            note="説明のみ依頼の実形式 fixture。",
        ),
    ]
