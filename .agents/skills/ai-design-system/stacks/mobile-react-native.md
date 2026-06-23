# React Native / Expo（Mobile）

`IDEAL.md` と `AESTHETIC.md` のスタック非依存原則を、React Native（iOS/Android）固有の制約に合わせるためのガイド。
モバイルは Web と違って **OS の HIG（Human Interface Guidelines）と aesthetic の衝突** を扱う必要がある。

---

## 1. SSOT 配置

| 形式 | ファイル | 注釈 |
|------|---------|------|
| TypeScript module | `design-system.config.ts` | プレーン TS。`export const designSystem = {...}` を root export |
| Expo theme | `design-system.config.ts` + `useTheme()` | NavigationContainer の theme 経路と統合する |
| Tamagui / Restyle | `tamagui.config.ts` / `restyle.theme.ts` | フレームワーク標準のテーマ定義そのものを SSOT として扱う |

`design-system.config.json`（aesthetic / antipatterns / conventions）は Web と共通形式で同梱する。

---

## 2. iOS / Android HIG との衝突

aesthetic.tone を選んだ後、**OS の慣習と衝突する箇所** を SSOT に書き残す。

| HIG 由来の機能 | iOS 標準 | Android 標準 | aesthetic との関係 |
|-------------|---------|------------|------------------|
| ナビゲーション | UINavigationBar（中央タイトル + 左戻る） | Material AppBar（左タイトル） | brutalist / editorial では非標準 navbar が必要なケース多 |
| ボタン形状 | iOS 17 で rounded rect 標準 | Material は filled / outlined / text | playful 以外で「全部 rounded」の default は外す検討 |
| Sheet / Modal | UIKit modal アニメーション | Material BottomSheet | aesthetic に合わない場合は custom sheet を実装 |
| Haptic feedback | UIImpactFeedbackGenerator | Vibrator API | aesthetic に応じて使う/使わないを決める。playful なら使う、minimal なら控えめに |
| System font | SF Pro / SF Mono | Roboto / Roboto Mono | **これに依存すると generic 化する**。後述 |

### System font に倒さない（重要）

iOS の `San Francisco` と Android の `Roboto` をそのまま使うのは、Web で言う Inter / Arial 直書きに相当する generic 化ルート。
どうしても system font に倒したい理由（読みやすさ最大化、ファイルサイズ削減等）がある場合のみ、`aesthetic.antiDirection` と矛盾しないかを SSOT で確認する。

代替: `expo-font` で custom font を読み込み、`design-system.config.ts` の `font.display` / `font.body` トークンに割り当てる。

### Dynamic Type への対応

iOS / Android ともに OS 設定でフォントサイズが変動する（accessibility large text）。SSOT は **絶対 px ではなく relative scale** で持つ。

```ts
import { PixelRatio } from 'react-native';

export const fontScale = PixelRatio.getFontScale(); // 1.0 baseline, larger if user enabled large text

export const typography = {
  body: { fontSize: 16 * fontScale, lineHeight: 24 * fontScale },
  display: { fontSize: 32 * fontScale, lineHeight: 40 * fontScale },
};
```

または `react-native` の `<Text allowFontScaling={true}>` をデフォルトにし、SSOT には base size のみ持つ。

### Safe area / notch

`react-native-safe-area-context` の inset は SSOT spacing と分離する:
- SSOT spacing: aesthetic に基づく余白
- safe area inset: OS hardware 由来の追加余白
**両者を混ぜない**。コンポーネントは `padding: spacing.md + insets.top` のように加算する。

---

## 3. 状態網羅と Pressed / Highlighted

Web の `:hover` / `:active` に該当する RN の状態:

| 状態 | RN での表現 | aesthetic 観点 |
|------|------------|---------------|
| pressed | `Pressable` の `pressed` callback / opacity / scale | playful なら scale + spring、minimal なら opacity のみ |
| disabled | `disabled={true}` + opacity | OS問わず opacity 0.38–0.5 が一般的 |
| focused | `onFocus` / `accessibilityState` | キーボード操作（Android tablet, iPad）で必須 |
| selected | radio / chip 等での独自管理 | aesthetic.accent を反映 |

`hover` は OS / hardware 依存（iPad with trackpad, Android with mouse）なので、デフォルトは無視できる。

---

## 4. アニメーションと aesthetic

`react-native-reanimated` を使う前提で:

- [ ] duration / easing が SSOT 経由（`Easing.bezier(...)` を直書きしない）
- [ ] `withSpring` / `withTiming` の使い分けが aesthetic に従う
  - playful: spring 多用
  - minimal: timing のみ、easing も standard
  - retro-futuristic: stepped easing（`Easing.steps`）等
- [ ] `prefers-reduced-motion` 相当: `AccessibilityInfo.isReduceMotionEnabled()` を読んで duration を 0 に倒す処理が SSOT 側にある
- [ ] アニメーションを使う「意味」が SSOT またはコンポーネント定義に記録されている

---

## 5. Dark mode と OS テーマ追従

iOS / Android ともに OS 設定での light/dark がある。

- [ ] `useColorScheme()` で OS の preference を読んでいる
- [ ] OS 追従だけでなくユーザー設定によるオーバーライド（"always light" / "always dark" / "system"）が可能
- [ ] dark mode は色トークンの差し替えのみで、aesthetic.tone 自体は不変（toneShift しない）

---

## 6. プラットフォーム差分の扱い

`Platform.OS === 'ios'` / `'android'` の分岐コードを撒く前に、SSOT に **どの差分は許容するか** を書く。

| 許容しがちな差分 | SSOT で扱う方針 |
|---------------|---------------|
| Shadow 表現（iOS は shadow*、Android は elevation） | `shadow` トークンが両 OS の値を保持する |
| Status bar style | `aesthetic.tone` に応じて light/dark を SSOT に記録 |
| Haptic 強度 | OS 関係なし。aesthetic で決める |
| Default font fallback | iOS = SF, Android = Roboto。custom font を読み込めばこの差分は消える |

---

## 7. 監査時の追加チェック

| 検出対象 | grep 例 |
|---------|---------|
| Generic system font 直書き | `rg -ttsx 'fontFamily.*("San Francisco"\|"Roboto"\|"-apple-system")'` |
| Inline numeric values | `rg -ttsx 'padding:\s*\d\|margin:\s*\d\|borderRadius:\s*\d'` |
| Easing 直書き | `rg -ttsx 'Easing\.bezier\|Easing\.inOut\|Easing\.linear'` |
| Shadow 直書き（iOS） | `rg -ttsx 'shadowOpacity\|shadowRadius'` |
| Elevation 直書き（Android） | `rg -ttsx 'elevation:\s*\d'` |
| Status bar inline | `rg -ttsx 'StatusBar.*barStyle'` |

---

## 8. Aesthetic と実装強度の整合（モバイル特化）

| aesthetic | 期待される実装 | NG |
|-----------|--------------|-----|
| brutally minimal | system-style avoidance、border のみ、spring 不使用、haptic なし | iOS-default 全採用、subtle blur、material elevation |
| playful / toy-like | spring easing 多用、原色アクセント、haptic 使用、丸み大 | linear easing、grayscale palette |
| editorial / magazine | 大胆 typography hierarchy、generous whitespace、写真主役の image 構成 | 等間隔 list cell、shadow card stack |
| retro-futuristic | pixel font / monospace、stepped easing、glitch effect、CRT vignette | Material design、smooth ease-out |
| industrial / utilitarian | 高密度 list、monospace、border-only divider、haptic 控えめ | hero 余白、装飾アイコン、過剰モーション |

---

## このガイドラインの使い方

- `BOOTSTRAP.md` Step 1 でモバイル（React Native / Expo）と判定された場合、Web 共通の `stacks/web-frontend.md` ではなくこのファイルを参照する
- aesthetic の選択は `AESTHETIC.md` の手順を踏襲。tone カタログは Web と共通
- iOS/Android 両 OS で aesthetic が同じ程度に成立するか、SSOT 上で明示的に確認する（片方の OS だけで成立する aesthetic はクロスプラットフォームの SSOT に向かない）
