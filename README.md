# Ancient & Medieval Japan - WorldMap（中世日本 - 世界地図）

**RimWorld 1.6用・開発試作版（一般公開未承認）。** 日本列島の形状は作者の旧版実ゲーム確認で合格。海上派閥拠点、山岳の一律入植禁止、霊山3座の山頂保護を修正した**新しい1.6プリセットとDLL**を同梱した。2026-10-17のLinux実ゲーム検証はPASS。高山の地理的な分布に対する作者の最終目視承認はまだ得ていないため、開発は継続する。

## GitHubからの導入（1.6）

1. `RimWorld/Mods/` で `git clone https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-WorldMap.git` を実行する。既存のcloneは `git pull` で更新する。
2. RimWorld **1.6** で **Harmony、Vanilla Expanded Framework、Worldbuilder、AMJ Environment、AMJ WorldMap** を有効化する。
3. RimWorldを再起動し、新規ワールド生成時に **Worldbuilderのプリセット選択画面**から **AMJ Japan World (Prototype)** を選択する。通常のランダムワールド設定から自動的に置き換わる方式ではない。

Modルート直下の必須ファイル：

```text
About/About.xml
Assemblies/AMJJapanWorldPresetRestore16.dll
Worldbuilder/AMJ_Japan_World_Prototype/Preset.xml
Worldbuilder/AMJ_Japan_World_Prototype/TerrainData.xml
```

## 実ゲーム検証と未確認範囲

**生成元：** WorldMap `d3783c6779525d75e1f750bc3e874492190fca1e`。修正版プリセット・DLLは [Project Actions #39042174500](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39042174500) の一回の手動生成から転送し、ソースXMLのGit Blob SHAを照合した。

Linux RimWorld 1.6で **海上・入植不能な派閥拠点0件、亜高山と高山の各入植可能地の存在、富士山・立山・白山の入植不能山頂3セル、同じ列島形状、実際の入植・セーブ・別プロセスでのロード、Unity ERROR 0** を確認。旧版の亜高山1,268→新版4,562タイル、高山33→55タイル（陸地50,810）。後者は陸地の約0.11%にとどまり、分布の最終目視判断は未了。

標高はGSI DEM10B z9から推定した現代のソースで、欠損した標高27タイルなど暫定値がある。中世の実測環境ではなく、季節・森林分布も完成していない。**1.7、Windows実ゲーム検証、既存固定ワールドセーブへの途中導入・差し替え、Steam Workshop公開は未承認・未確認。** 既存セーブへのMod削除は行わず、新プリセットは新規ワールドで使用すること。

- [正式設計・受入条件](Docs/Design.md)
- [実行結果JSON](Docs/Data/WorldMapNativeAcceptance16-20261017.json)
- [生成・標高・生態分布QA](Docs/Data/WorldMapRegionalQA16-20261017.json)
- [GIS/JMA/GSI来歴とライセンス](Docs/DataProvenance.md)
- [作業状態](Docs/Coordination.md)
- [Modメタデータ](About/About.xml)
- [生成ソース](Tools/Production/)
- [地理・気候研究ソース](Tools/Research/)
