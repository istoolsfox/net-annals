#!/usr/bin/env bash
# 对外发布：把「已提交」的 site/ 同步到 gh-pages 分支并推送 → GitHub Pages
# https://istoolsfox.github.io/net-annals/
# 纪律：只发布 HEAD 已提交内容（git archive），不取工作区 WIP——半成品数据不上公网。
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

WORK="$(mktemp -d)"
cleanup() {
  cd "$REPO"  # 脚本可能停在 ghpages cwd 里，先离开再拆除，避免 cwd 被删后 git 报错
  git worktree remove --force "$WORK/ghpages" 2>/dev/null || true
  rm -rf "$WORK"
  git worktree prune
}
trap cleanup EXIT

echo "==> 1/3 导出 HEAD 已提交的 site/"
git archive HEAD site/ | tar -x -C "$WORK"
# 例外：site/data.json 是 build 产物（main 仓 gitignore），Pages 镜像历来显式收录。
# 取工作区副本；运行前先跑 build 保证它与已提交数据同代（WIP 数据未 build 就不会混入）。
if [ ! -f site/data.json ]; then
  echo "❌ 缺 site/data.json：先跑 scripts/build.sh 再发布" >&2
  exit 1
fi
cp site/data.json "$WORK/site/data.json"
python3 -c "import json;d=json.load(open('$WORK/site/data.json'));ev=d.get('events',d);print('    data.json 事件数:',len(ev))"

echo "==> 2/3 同步到 gh-pages 工作树"
git worktree prune
git worktree add --quiet "$WORK/ghpages" gh-pages
# .git 指针文件与 .nojekyll 必须排除在 --delete 之外，否则 worktree 被拆断
rsync -a --delete --exclude='.git' --exclude='.nojekyll' "$WORK/site/" "$WORK/ghpages/"

cd "$WORK/ghpages"
git rev-parse --is-inside-work-tree >/dev/null  # worktree 健全性：坏了立刻炸，不许静默
if [ -z "$(git status --porcelain)" ]; then
  echo "✅ gh-pages 与 HEAD 一致，无需发布"
  exit 0
fi
git add -A
git commit --quiet -m "mirror: sync from main $(git -C "$REPO" log -1 --format='%h %s' | cut -c1-70)"
git push --quiet origin gh-pages

echo "==> 3/3 清理"
echo "✅ 已发布 → https://istoolsfox.github.io/net-annals/"
