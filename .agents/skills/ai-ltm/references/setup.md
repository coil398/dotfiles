# ai-ltm 初回セットアップガイド

`~/ai-ltm-data/memory.db` が存在しない場合にこの手順を実行する。

---

## 1. 既存リポジトリがある場合（別マシンで使用済み）

```bash
git clone <リモートリポジトリURL> ~/ai-ltm-data
```

クローン後、memory.db が含まれていれば完了。

## 2. 新規セットアップの場合

```bash
mkdir -p ~/ai-ltm-data && cd ~/ai-ltm-data
git init
```

スキーマを初期化する（`init.sql` はこのスキルと同じディレクトリにある）:

```bash
sqlite3 ~/ai-ltm-data/memory.db < <このスキルのディレクトリ>/init.sql
```

`.gitignore` をコピー:

```bash
cp <このスキルのディレクトリ>/.gitignore ~/ai-ltm-data/.gitignore
```

## 3. リモートリポジトリの接続

GitHubにプライベートリポジトリを作成するようユーザーに案内する:

> リモートリポジトリが必要です。GitHubでプライベートリポジトリを作成してください。
> 作成後、URLを教えてください（例: `git@github.com:<user>/ai-ltm-data.git`）。

ユーザーからURLを受け取ったら:

```bash
cd ~/ai-ltm-data
git remote add origin <URL>
git add memory.db .gitignore
git commit -m "init: AI長期記憶システム初期化"
git push -u origin main
```

## 注意事項

- セットアップはユーザーに確認を取ってから実行すること
- リポジトリは必ず**プライベート**で作成する（記憶に機密情報が混入するリスクを最小化）
