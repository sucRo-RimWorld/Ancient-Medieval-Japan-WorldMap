# Ancient & Medieval Japan - WorldMap（中世日本 - 世界地図）

**開発中／RimWorld 1.6試作版。** 日本列島の形状は作者が実ゲームで確認済み。現在は海上の派閥拠点、亜高山・高山の不足、山地の入植可能性、霊山の山頂制限を修正・検証中。**これらを解決するまでWorldMapの開発を保留しない。**

## 重要：git cloneしただけではワールドを選択できない

このリポジトリは**ソース管理用**。 `About/About.xml` はこのリポジトリ直下にあるが、Worldbuilderが表示するための**生成済みプリセット2ファイルと実行時DLLはリポジトリに含まれていない**。そのため、現行の `main` をRimWorldのModsフォルダにgit cloneしても、ワールド生成画面には **AMJ Japan World (Prototype)** が表示されない。これは現在の配布方法の未完成部分であり、読み込み順序の問題ではない。

**既存の実ゲーム確認済み1.6形状をすぐ試す場合：**

1. [Project Actions #39022443969](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39022443969) から [AMJ-Japan-World-Prototype-1.6 のZIP成果物](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39022443969/artifacts/12097720526) を取得する（GitHubでProjectへのアクセスが必要な場合あり）。
2. ZIPを展開した**Modルート**に `About/About.xml`, `Assemblies/AMJJapanWorldPresetRestore16.dll`, `Worldbuilder/AMJ_Japan_World_Prototype/Preset.xml`, `Worldbuilder/AMJ_Japan_World_Prototype/TerrainData.xml` が揃っていることを確認する。
3. `RimWorld/Mods/AMJ-Japan-World-Prototype/` へそのフォルダ構成を置き、**Harmony、Vanilla Expanded Framework、Worldbuilder、AMJ Environment** を有効化する。
4. RimWorld **1.6** を起動し、**Worldbuilderのプリセット選択画面**で `AMJ Japan World (Prototype)` を選ぶ。通常のランダムワールド作成一覧に独立した地図選択肢として出ることは保証していない。

**注意：** これは元の1.6試作成果物。形状確認には利用できるが、その後GitHub上で修正した**海上派閥拠点、標高データ、入植可能な山地、霊山の制限を反映した新ビルドではない**。修正版の新たな実ゲーム受入は未完了で、1.7対応も未確認。既存セーブへの途中導入や削除は推奨しない。上記Actions成果物は保持期限付きである。

## 開発ソース

- [正式設計、作業状態・実ゲーム検証範囲](Docs/Design.md)
- [現在の作業引き継ぎ](Docs/Coordination.md)
- [本番Modメタデータの正本](About/About.xml)
- [ワールド生成・復元用C#とビルドPython](Tools/Production/)
- [海岸線・DEM10B標高・気候の入力処理](Tools/Research/)
- [旧Project側の研究履歴](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/blob/main/Docs/Research/JapanWorldMapCandidate.md)

本番生成スクリプト `Tools/Production/build_japan_world_preset16.py` は、このリポジトリのルート `About/About.xml` をパッケージへ複製する。独立したModとしての公開は未承認。地図を構成する第三者原データ・ゲーム本体・Worldbuilderバイナリの無断再配布は行わない。
