# PHILOSOPHY.md — 中国互联网编年史（net-annals）〔草稿 v0.1，待用户拍板〕

> 由 refinery A-greenfield 流程起草于 2026-10-24，考古依据：app.js 头注释（v3 分层架构自述）、各页内联脚本惯用法、nginx 生产配置。

## 一、宗旨

一部"精确到日、每条可溯源"的中国互联网编年史。**内容可信 > 体验顺滑 > 代码优雅**，三者冲突时按此序取舍。

## 二、设计哲学

1. **零依赖纯静态**：不引任何 JS 库/框架/构建链；浏览器原生 API 够用就用（DecompressionStream、IntersectionObserver、grid-template-rows 动画）。数据即文件（JSON + 预压缩 .gz），nginx 直接服务。
2. **分层单向**（app.js）：Toolbar(控制) → Store(状态+选择器，唯一事实源) → Timeline(纯渲染)。渲染幂等可重入；懒加载只做性能优化、不做正确性依赖（几何兜底 + IO 双保险）。
3. **性能预算意识**：4993+ 事件的长卷必须分帧渲染（12ms/帧）、分片惰性加载、隐藏内容懒构建 DOM；任何新增交互不得引入全量重渲。
4. **缓存纪律**：改任何被 ?v= 引用的静态资源，必须同步 bump 全部引用页的版本号；data 分片版本锚定 manifest.generated。
5. **渐进降级**： DecompressionStream/IntersectionObserver/clipboard 等 API 缺失时必须有可用回退；prefers-reduced-motion 必须降级。

## 三、风格三层（强约束 → 建议 → 见仁见智）

- **强约束**：中文注释、'use strict'、模板字符串拼 DOM 时一切动态值过 esc()/safeUrl()；字符串→DOM 只用 innerHTML 于可信模板；事件一律委托到容器（#timeline 模式）。
- **建议**：CSS 自定义属性做主题变量；单文件页面（每子页自带 <style> 与 <script>）；mono 字体标注元信息。
- **见仁见智**：命名风格、注释密度。

## 四、禁区

- 禁止引入构建工具/框架/npm 依赖（除非用户明示）。
- 禁止在渲染路径里做同步网络请求。
- 禁止绕过 Store 直接改视图状态；禁止让 Timeline 依赖 Toolbar。
- 禁止为了"优化"破坏每条可溯源原则（来源数据一个都不能少）。

## 五、机器命令（AI 可直接执行的检查）

- `node --check site/app.js`（及各页内联脚本抽检）须 0 退出。
- 本地 `python -m http.server` + 浏览器冒烟考卷（tests/smoke.mjs）须全绿。
- 部署前 diff 检查：任何被 ?v= 引用文件的改动必须伴随引用页版本号变更，否则视为违规。
