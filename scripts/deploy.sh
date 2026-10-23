#!/usr/bin/env bash
# 一键发布：构建校验 → rsync 到 toolsfox 服务器
# 用法：./scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 1/2 构建校验合并"
python3 scripts/normalize.py
python3 scripts/dedup.py
python3 scripts/build.py
python3 scripts/geo_match.py
python3 scripts/build_geo.py
python3 scripts/build_persons.py
python3 scripts/build_entities.py

echo "==> 2/2 发布到 toolsfox.top"
rsync -az --delete --delete-excluded --exclude=/data.json site/ toolsfox:/var/www/net-annals/

echo
echo "✅ 已发布 → https://toolsfox.top/net-annals/"
