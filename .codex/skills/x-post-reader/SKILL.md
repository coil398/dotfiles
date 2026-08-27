---
name: "x-post-reader"
description: "X/Twitter の投稿URLを確実に読む。x.com / twitter.com の status URL が入力されたら、X本体での取得失敗を待たず FxTwitter API v2 を優先して本文・引用・スレッド・メディア情報を取得する。『このX』『この投稿』『これどう』のような依頼でも自動適用する。"
argument-hint: "[X/Twitter post URL]"
---

# X Post Reader

X/Twitter の公開投稿を読むときは、X のHTMLページを主経路にしない。FxEmbed/FxTwitter の JSON API を優先する。

## Trigger

次のURLがユーザー入力に含まれたら、明示的な `/x-post-reader` 指定がなくてもこのスキルを使う。

- `https://x.com/<handle>/status/<id>`
- `https://x.com/i/status/<id>`
- `https://twitter.com/<handle>/status/<id>`
- `https://mobile.twitter.com/<handle>/status/<id>`
- `status` の代わりに `statuses` を使う同等URL

## Retrieval

1. URLから投稿IDを抽出する。基本形は `/(?:status|statuses)/(\d{2,20})`。
2. クエリ文字列や `photo/1` などの後続パスは取得キーに使わない。
3. 次のAPIを最優先で取得する。

   `https://api.fxtwitter.com/2/status/<id>`

4. ランタイムにHTTP取得ツールがある場合はそれを使う。shell が使える場合は次でもよい。

   `curl -fsSL --max-time 20 -H 'Accept: application/json' -A 'coil398-x-post-reader/1.0' 'https://api.fxtwitter.com/2/status/<id>'`

5. JSON の `code` が `200` で、`status` が存在することを確認してから内容として扱う。
6. 主に次を読む。
   - `status.text`: 投稿本文
   - `status.author`: 投稿者
   - `status.created_at`: 投稿日時
   - `status.quote`: 引用元
   - `status.media`: 画像・動画・外部メディア
   - `thread`: 同一会話・スレッド文脈

## Media

画像や動画が論点なら、`status.media` にある実メディアを確認できるランタイムでは実物まで取得して判断する。本文だけから動画・画像の内容を推測しない。

人間向けの埋め込みURLが必要な場合だけ、元URLの `x.com` を `fixupx.com` に置換する。エージェントの内容取得には JSON API を使う。

## Failure policy

- X本体の取得に失敗しただけで「Xが見えない」「投稿を確認できない」と返さない。先に FxTwitter API を試す。
- APIが tombstone / deleted / private / unavailable を返した場合は、その状態をそのまま報告する。
- APIが取得できた場合、検索結果の断片や転載から本文を再構成しない。
- API自体のネットワーク失敗時だけ、失敗した取得経路を明示する。内容を推測で補わない。

## Privacy

Cookie、Xの認証情報、個人トークンは送らない。公開投稿IDだけを FxTwitter API に渡す。
