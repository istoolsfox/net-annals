#!/usr/bin/env bash
# API 侧一键发布：同步脚本/模板 → 拉齐站点数据工件 → 重建 API 库 → 重启服务 → 冒烟。
# （site/ 静态站点发布走 deploy.sh，两条线互不干扰；nginx/systemd 配置变更见 docs/SERVER.md）
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="netannals:netannals-pipeline/repo"

echo "==> 1/4 同步 API 代码与贡献模板"
rsync -az scripts/api scripts/api_server.py scripts/api_keys.py \
      scripts/build_api_db.py scripts/api_smoke_test.py \
      scripts/validate_events.py scripts/new_entry.py "$REPO/scripts/"
rsync -az templates "$REPO/"

echo "==> 2/4 拉齐数据源并重建 API 库"
ssh netannals "cd netannals-pipeline/repo && \
  (git pull --ff-only || echo '⚠ git pull 失败，用仓库现状构建（人工检查）'); \
  cp /var/www/net-annals/persons/data.json site/persons/data.json; \
  cp /var/www/net-annals/persons/groups.json site/persons/groups.json; \
  cp /var/www/net-annals/entities/data.json site/entities/data.json; \
  cp /var/www/net-annals/works/data.json site/works/data.json; \
  ../.venv/bin/python scripts/build_api_db.py && \
  sudo systemctl restart netannals-api && sleep 2 && \
  sudo systemctl is-active netannals-api"

echo "==> 3/4 冒烟"
ssh netannals "cd netannals-pipeline/repo && ../.venv/bin/python scripts/api_smoke_test.py http://127.0.0.1:8400 | tail -4"

echo
echo "✅ API 已发布 → 服务器 127.0.0.1:8400（对外经 https://toolsfox.cn/api/）"
