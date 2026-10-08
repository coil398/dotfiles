# .githooks

- `pre-commit` は全repoへ作用するdispatcher。既存のsecret/SSOT/layout検査、ローカルhookへのdispatch、同じ物理pathを呼ばない再帰防止を保つ。検査と明示bypassの正本はスクリプトにあり、通常修復でbypassを使わない。
- gitleaks導入経路は環境別のinstallスクリプトを読む。未導入時の警告と、検出・検査失敗による非ゼロ終了を混同しない。
