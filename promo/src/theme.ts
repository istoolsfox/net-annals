// 全片视觉 tokens —— 取自站点设计语言（深墨纸感 + 金色衬线长卷）
export const C = {
  bg: '#0c0d10', bg2: '#101218', panel: '#16181d', line: '#2a2d35', line2: '#3a3e48',
  text: '#e8e4da', dim: '#9a958a', faint: '#66625a',
  gold: '#c9a86a', goldBright: '#e0c48e', red: '#b0493e',
};
export const SERIF = '"Songti SC","Noto Serif SC","SimSun",serif';
export const SANS = '"Microsoft YaHei","PingFang SC",sans-serif';
export const MONO = 'Consolas,"Cascadia Code",ui-monospace,monospace';
// 动效性格：精致高端 —— 无弹跳、对称缓动、长 hold
export const EASE = [0.33, 0, 0.15, 1] as const;
export const FADE = 8; // 每镜头首尾黑场过渡帧数
