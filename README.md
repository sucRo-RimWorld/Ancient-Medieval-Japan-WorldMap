# Ancient & Medieval Japan - WorldMap（中世日本 - 世界地図）

**RimWorld 1.6用の開発試作版。日本列島の形状は作者の実ゲーム確認で合格。** 4件の問題（海上派閥拠点、亜高山・高山の少なさ、通常山岳の入植可能性、富士山・立山・白山の山頂制限）は修正・実ゲーム受入が完了するまで開発を継続する。

## GitHubからの導入（1.6）

このリポジトリは **git clone後に必要なModデータが揃う配置**となっている。生成用ソースだけでなく、**以前の1.6実ゲーム確認済みプリセットと実行DLL**を同梱している。

1. `RimWorld/Mods/` で `git clone https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-WorldMap.git` を実行する。既存のcloneがある場合は `git pull` で更新する。
2. RimWorld **1.6** で **Harmony、Vanilla Expanded Framework、Worldbuilder、AMJ Environment、AMJ WorldMap** を有効化する。
3. RimWorldを再起動し、新規ワールド生成時に **Worldbuilderのプリセット選択画面**から **AMJ Japan World (Prototype)** を選択する。通常のランダムワールド設定に地図が自動で現れる方式ではない。

配置の基準（`RimWorld/Mods/Ancient-Medieval-Japan-WorldMap/`直下）：

```text
About/About.xml
Assemblies/AMJJapanWorldPresetRestore16.dll
Worldbuilder/AMJ_Japan_World_Prototype/Preset.xml
Worldbuilder/AMJ_Japan_World_Prototype/TerrainData.xml
```

**重要 — 同梱内容のバージョン：** `Assemblies` と `Worldbuilder` の3ファイルは **Project Actions #39022443969で検証された元の2026-10-17形状試作版**。後から変更した新しい海上派閥拠点・DEM10B標高・高山入植可能性・霊山山頂のソース修正は**まだ再ビルドされておらず、この配布ファイルには反映されていない**。その4件を未修正のまま遊ぶための試作版であることに注意。1.7は未確認。既存の固定マップセーブへの途中導入・削除には非対応。

## 実ゲーム検証・来歴

原型のLinux RimWorld 1.6で、ワールド生成・拠点形成・セーブ・ロードを [Project Actions #39022443969](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39022443969) で確認済み。作者による形状の目視確認も合格。今回のリポジトリ取り込み後の別環境でのクローン動作は、**同一プリセット/DLLのバイト照合とファイル配置の静的確認であり、新たな実ゲームPASSではない**。

- [正式設計・作業とテストの受入条件](Docs/Design.md)
- [作業状態と担当区分](Docs/Coordination.md)
- [旧原型ZIPのデータソース・ライセンス表記](Docs/DataProvenance.md)
- [Modメタデータの正本](About/About.xml)
- [今後のワールド生成・復元の実装ソース](Tools/Production/)
- [海岸線・新しいDEM10B・気候モデルの生成ソース](Tools/Research/)
- [Project側の旧研究履歴](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/blob/main/Docs/Research/JapanWorldMapCandidate.md)

Steam Workshopでの正式公開は未承認。次に新しい修正済みプリセットを生成したときは、**元の旧試作版であることを明示したまま放置せず、実ゲーム検証後に同梱DLL/XMLを差し替える**。
