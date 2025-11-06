!!!warning "訳注"
    本書は、訳者：[wakuto](https://github.com/wakuto) による **非公式の** 日本語版です。
    翻訳にはAIを用いており、内容の正しさは一切保証できません！
    日本語版の翻訳の誤りについては XiangShan 公式ではなく、

    * 日本語版リポジトリ：[https://github.com/wakuto/XiangShan-Design-Doc/tree/japanese](https://github.com/wakuto/XiangShan-Design-Doc/tree/japanese)

    にお願いします。

# 前書き {.unnumbered .unlisted}

本書は「香山オープンソースプロセッサ設計ドキュメント」であり、{{processor_name}} のマイクロアーキテクチャ実装を詳細に解説する。

最新版は以下の経路から入手できる。

* ウェブ版：[https://docs.xiangshan.cc/projects/design/](https://docs.xiangshan.cc/projects/design/)
* PDF 版：[https://github.com/OpenXiangShan/XiangShan-Design-Doc/releases](https://github.com/OpenXiangShan/XiangShan-Design-Doc/releases)

その他の資料は香山ドキュメントサイト [docs.xiangshan.cc](https://docs.xiangshan.cc/) を参照されたい。

本書の原文は中国語で、GitHub にホストされている。翻訳には Weblate プラットフォームを利用しており、校正・誤り修正・翻訳への参加を歓迎する。

## 免責事項 {.unnumbered .unlisted}

著作権 © 2024 - 2025 香山オープンソースプロセッサチーム・北京開源芯片研究院

本書は「[クリエイティブ・コモンズ 表示 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja)」ライセンスで公開されている。ライセンス条項に従い、適切なクレジットを明示し、元のライセンスを提示し、原文からの変更有無を示す限り、自由に利用・改変・再配布できる。詳細な条件はクリエイティブ・コモンズが公表する完全な法的文書を参照のこと。

本書は段階的な情報を提供するものであり、状況に応じて随時更新される場合がある。特段の取り決めがない限り、本書中の記載・情報・助言はいかなる明示または黙示の保証も伴わない。

## 版情報 {.unnumbered .unlisted}

| 日付 | 版 | 説明   |
| ---- | -- | ------ |
|      |    | 初版発行 |
