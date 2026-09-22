"""Ensure evaluation fixtures parse and the contrast pair stays distinct."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import transcript as tr  # noqa: E402
from jev_hooks.tests.eval_cases import ALLOW, CONTINUE, cases  # noqa: E402


class EvalCaseShapeTests(unittest.TestCase):
    def test_contrast_pair_and_parse(self) -> None:
        by_id = {c.case_id: c for c in cases()}
        cont = by_id["correction_why_restrict_in_progress"]
        expl = by_id["same_question_explain_only"]
        self.assertEqual(cont.family, CONTINUE)
        self.assertEqual(expl.family, ALLOW)
        self.assertIn("なぜホーム画面でしか動かないように制限している", "\n".join(cont.lines))
        self.assertIn("なぜホーム画面でしか動かないように制限している", "\n".join(expl.lines))
        ctx_c = tr.parse_lines(cont.lines, cont.turn_id)
        ctx_e = tr.parse_lines(expl.lines, expl.turn_id)
        self.assertTrue(any("実装" in m.text for m in ctx_c.user_messages))
        self.assertTrue(any("説明" in m.text or "理由" in m.text for m in ctx_e.user_messages))
        for case in cases():
            ctx = tr.parse_lines(case.lines, case.turn_id)
            self.assertGreaterEqual(len(case.lines), 3, case.case_id)
            self.assertTrue(ctx.user_messages or ctx.window_truncated, case.case_id)


if __name__ == "__main__":
    unittest.main()
