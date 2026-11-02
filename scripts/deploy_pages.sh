#!/usr/bin/env bash
# 对外发布：把「已提交」的 site/ 同步到 gh-pages 分支并推送 → GitHub Pages
# https://istoolsfox.github.io/net-annals/
# 纪律：只发布 HEAD 已提交内容（git archive），不取工作区 WIP——半成品数据不上公网。
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

WORK="$(mktemp -d)"
cleanup() { git worktree remove --force "$WORK/ghpages" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT

echo "==> 1/3 导出 HEAD 已提交的 site/"
git archive HEAD site/ | tar -x -C "$WORK"

echo "==> 2/3 同步到 gh-pages 工作树"
git worktree add --quiet "$WORK/ghpages" gh-pages
rsync -a --delete --exclude='.nojekyll' "$WORK/site/" "$WORK/ghpages/"

cd "$WORK/ghpages"
if [ -z "$(git status --porcelain)" ]; then
  echo "✅ gh-pages 与 HEAD 一致，无需发布"
  exit 0
fi
git add -A
git commit --quiet -m "mirror: sync from main $(git -C "$REPO" log -1 --format='%h %s' | cut -c1-70)"
git push --quiet origin gh-pages

echo "==> 3/3 清理"
echo "✅ 已发布 → https://istoolsfox.github.io/net-annals/"
