# 宣传片源工程（video-shotcraft 自由创作模式）

26 秒 1080p30 宣传片，Remotion 实现，素材为 toolsfox.cn 真实页面截图。
构建目录需纯 ASCII 路径（Remotion 静态服务对非 ASCII 项目路径 404）：
`C:\Users\PC\Desktop\netannals-promo`（本目录 src 同步自那里）。

重渲：构建目录内 `npx remotion render src/index.ts Promo out/promo.mp4`
（改纹理后加 `--no-cache` 强制重建 webpack 缓存）。
成片：04-素材/宣传视频/中国互联网编年史_宣传片_20261025.mp4
