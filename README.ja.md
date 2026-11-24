<div align="center">

# 衣姿 PoseWear

絵を描くとき、写真を撮るとき、AI で画像を作るときの参考素材を探す場所。

ポーズ・衣装・人物・表情など 12 の素材集に、中英プロンプト付き。
素材を選べばそのままブラウザで生成でき、組み合わせを AI エージェントに渡すこともできます。

[オンライン版](https://posewear.pages.dev/) · [简体中文](README.md) · [English](README.en.md) · [更新履歴](CHANGELOG.md)

> **偽サイトにご注意**：公式の入口は [posewear.pages.dev](https://posewear.pages.dev/) と本リポジトリのみです。PoseWear に Windows / Android アプリはなく、ネットドライブ等でインストールパッケージを配布することもありません。posewear.cn など公式を名乗り exe / apk のダウンロードを提供するサイトはすべて偽物です。ダウンロードせず、API キーを入力しないでください。

![衣装ライブラリ](docs/home-ja.jpg)

</div>

## 素材の探し方

- **ポーズは線画と深度画像のペア**：同じポーズ・同じアングルの両面がそろっています。カードの番号を押すと裏返り、両方を生成に使うこともできます。
- **フローティング作業台で集める**：閲覧しながらカードの ＋ を押すだけで下部の作業台に入ります。そこから生成したり、プロンプトと画像リンクをまとめてコピーしたりできます。
- **本格スタジオでは自由に組み合わせ**：人物・衣装・ポーズに、表情・髪型・背景・照明・小道具・家具を加えて。使う素材は1つでも、プロンプトだけでも大丈夫です。自分の写真をアップロードすれば試着の比較もできます。
- 生成した画像は「生成履歴」に保存され、表示・ダウンロード・ZIP 書き出しができます。

![スタジオ](docs/studio-ja.jpg)

<table><tr>
<td width="30%"><img src="docs/mobile-ja.jpg" alt="スマートフォンでの閲覧"><br><sub>スマホでも素材探し</sub></td>
<td><img src="docs/dark-ja.jpg" alt="ダークモード"><br><sub>ダークモード（初期設定はシステム連動）</sub></td>
</tr></table>

画面は日本語・中国語・英語の3言語対応。素材の説明は中国語と英語を切り替えられます。

## 生成方法は3つから

**自分の API キーで** — OpenAI、Gemini、豆包 Seedream のキー、または OpenAI / Gemini / xAI 互換の中継サービスを設定します。ブラウザから直接送るか、このサイトのプロキシ経由（http/https・任意ポート対応）で送れます。

**この端末のモデルで** — ComfyUI や stable-diffusion.cpp を動かしているなら、ローカルエンジンに接続して生成できます。画像が端末の外に出ることはありません。[設定ガイド](docs/local-engines.md)

**AI エージェントに任せる** — リポジトリには MCP サーバーが入っていて、エージェントが素材検索、角度指定の取得、プロンプトと参照リンクの組み立てを自分で行えます：

```sh
codex mcp add posewear -- node "$PWD/mcp/server.mjs"
```

あとは「横向きの座りポーズに春服を合わせて、プロンプトと参考リンクをちょうだい」と頼むだけです。[MCP ガイド](mcp/README.md)

## ローカルで動かす

Node.js 22.12 以上が必要です：

```sh
git clone https://github.com/atuizz/posewear.git
cd posewear
npm ci
npm start
```

http://127.0.0.1:8787/ を開いてください。閲覧・お気に入り・コピーにアカウントやキーは不要です。素材目録は初回にオンラインから読み込み、画像は必要なときに読み込みます。

お気に入り・設定・API キーはお使いのブラウザ内にだけ保存され、生成履歴もブラウザのデータベースに保存されます。サイトデータを消せば一緒に消えます。

## 開発

素の JS と Python ビルド、Cloudflare Pages のみで、フレームワークは使っていません。ビルド・素材準備・テスト・デプロイの手順は [AGENTS.md](AGENTS.md) にまとめています。回帰テストは `npm test` です。

現在のバージョンは **v1.3.1**（2026-11-24）：カスタム中継へのプロキシ転送と、画像の長期キャッシュを復旧しました。[全バージョン履歴](CHANGELOG.md)

## 素材の出典とライセンス

コード・画面文案・ビルドスクリプトは [MIT](LICENSE) です。画像の権利は各出典に帰属します。自前で公開する場合は出典表示を残してください：

| 素材 | 出典 |
| --- | --- |
| ポーズ、深度ポーズ、衣装、アニメ衣装 | ギア / @giaaibusi。商用・転載は作者に確認してください。[線画](https://ai-pose-gallery.pages.dev/) · [深度](https://ai-pose-depth-gallery.pages.dev/) · [衣装](https://ai-costume-gallery.pages.dev/) · [アニメ衣装](https://ai-costume-anime-gallery.pages.dev/) |
| 人物 | @agi_aibusi の架空 AI 人物、CC0。作者はそのままの一括転載を控えるよう求めています。[AI Portrait Gallery](https://ai-portrait-gallery.pages.dev/) |
| 髪型と一部のアニメ衣装 | たき AI / CharaDB。タグは CC0、画像は元サイトから読み込みます。[CharaDB](https://charadb-2fi.pages.dev/) |
| 表情 | WaveSpeed AI Emotion Gallery。頭部モデルは ICT FaceKit（© USC Institute for Creative Technologies、MIT） |
| 時代衣装、背景、照明、小道具、家具 | Shisei / wquguru、CC0 1.0 |

インスピレーションをくれた [gen-ai-pose-image](https://github.com/wzc520pyfm/gen-ai-pose-image) と [nvzhuang](https://github.com/paipiange/nvzhuang) に感謝します。
