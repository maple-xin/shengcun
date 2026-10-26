# 森林 / 厨房生存挑战 · GLB 模型包

实际交付 **41 个 GLB，模型合计约 4.8 MB**。贴图均内嵌，模型无需另外下载贴图文件。

| 内容 | 数量 | 路径 |
|---|---:|---|
| 已摆好的森林、厨房场景 | 2 | `models/stages/` |
| 森林树木、灌木、草与石头 | 12 | `models/forest/` |
| 厨房家具、电器、甜品 | 15 | `models/kitchen/` |
| 独立地砖、障碍物、装饰 | 10 | `models/common/` |
| 带动画的方块男孩、女孩 | 2 | `models/common/player-*.glb` |

这是可编辑的低多边形模型基础包。实际预览见 `previews/`；概念参考图里的精细材质、景深和特效需要在游戏里继续制作。包内不包含完成的游戏逻辑。

## 上传 GitHub Pages

1. 解压 ZIP。把**解压后的内容**上传到仓库根目录，确保 `index.html`、`models`、`vendor` 等直接位于根目录。不要只上传 ZIP 文件。包括文件夹在内80 个文件，可分批上传。
2. 仓库 `Settings → Pages → Build and deployment → Source: Deploy from a branch`，选择 `main` 和 `/(root)`，保存，等待部署完成。免费账户通常使用公开仓库。[GitHub 官方说明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
3. 打开 Pages 给出的站点地址。在预览页选择模型，点 **Copy model URL**，把这个 `.glb` 链接交给 Loopit。

假设账号为 `YOURNAME`，仓库为 `YOURREPO`：

```text
预览页：https://YOURNAME.github.io/YOURREPO/
森林：https://YOURNAME.github.io/YOURREPO/models/stages/forest_stage.glb
厨房：https://YOURNAME.github.io/YOURREPO/models/stages/kitchen_stage.glb
角色：https://YOURNAME.github.io/YOURREPO/models/common/player-boy.glb
陨石：https://YOURNAME.github.io/YOURREPO/models/common/hazard_meteor.glb
擀面杖：https://YOURNAME.github.io/YOURREPO/models/common/hazard_rolling_pin.glb
清单：https://YOURNAME.github.io/YOURREPO/manifest.json
```

替换账号和仓库名，大小写与文件路径一致。不要使用 `github.com/.../blob/...` 网页链接。用户/组织主页仓库则没有 `/YOURREPO/` 这一段。

## 建议怎样导入 Loopit

先用 `LOOPIT-IMPORT.txt`，把其中的地址替换为你实际的 Pages 链接。**先做森林第一关**，确认手机移动、碰撞、翻砖正常，再扩展关卡和厨房。

- 每次加载一个完整场景和一个角色。完整场景已经摆好了树、家具等，不需要把单体装饰再加载一遍。
- 两个场景各有 **12 × 12 = 144 块地砖**，每块独立父节点名为 `tile_00_00` 至 `tile_11_11`。不要将整个平台合并成一块。
- Y 向上；地砖顶面 Y=0；网格间距 1；砖面宽 0.97；地砖原点位于顶面中心。列号控制 X，行号控制 Z；位置为 `(column−5.5, 0, row−5.5)`。
- 场景含 `tiles`、`decor`、`player_spawn` 分组/节点。玩家没有烘焙进场景，需单独加载；两个人物建议初始缩放 **0.5**，实际根据碰撞胶囊调整。
- 森林、厨房之间的地砖结构一致，可以复用玩法。每块砖用一个简单格子碰撞体；砖掉落时同步关闭碰撞。平台下方没有隐藏整块地板。
- 人物各有 27 个动画片段。常用：`idle`、`walk`、`sprint`、`die`；完整名称见 `manifest.json`。不含跳跃片段。
- 摆景仅负责视觉，玩家活动范围限制在有效地砖内。坠落、预警、爆炸击退、火焰、音效均由 Loopit 运行时实现。

## 手机性能与地砖控制

完整森林约 15.6 万三角形，厨房约 22.6 万；这是几何预算，不代表已经完成手机帧率测试。优先使用实例化地砖、简单碰撞、少量实时阴影和低成本特效。

可选 `integration/tile-grid.js` 适用于 Three.js：

```js
import { prepareTiles } from './integration/tile-grid.js';
const tiles = prepareTiles(gltf.scene, THREE); // 导入完成后调用一次
tiles.setTile('tile_05_05', { flip: Math.PI / 2 });
tiles.setTile('tile_05_05', { drop: 2 });
tiles.setTile('tile_05_05', { visible: false });
tiles.reset();
```

这个函数将重复砖面合批，同时保留每格控制。启用后须用 `setTile` 控制显示，直接改原节点 `visible` 不会修改实例。每次调用的状态是完整状态，不是增量；隐藏后传 `{flip:...}` 会重新显示该砖。自定义导入器也可以不使用此辅助文件，直接控制 GLB 节点。

## 已检查与边界

已检查全部 GLB 头、缓冲区、内嵌贴图、有限坐标范围及 SHA-256；两场景各有 144 个独立地砖节点。来源模型和原创新模型均经过 Blender 导入/渲染检查。预览页提供 **Check all 41 GLBs**，可在你的 Pages 域名下复查加载与地砖隐藏/还原。

浏览器预览需要通过 HTTP(S) 打开。直接双击本地 HTML 可能因浏览器安全规则无法加载；本地可运行 `python3 -m http.server 5206` 后访问 `http://localhost:5206/`。

模型为 CC0；Three.js 查看器运行库为 MIT，随包保留授权。具体来源与再分发记录见 `CREDITS.md` 和 `licenses/`。未代你创建 GitHub 仓库、发布 Pages 或验证 Loopit 的具体导入环境。
