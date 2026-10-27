#!/usr/bin/env bash
# 一键发布：构建校验 → rsync 到 netannals 服务器（https://toolsfox.cn）
# 旧 toolsfox 服务器对 /net-annals 路径做 301 过渡；如需回滚：rsync site/ toolsfox:/var/www/net-annals/
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 1/2 构建校验合并"
python3 scripts/normalize.py
python3 scripts/dedup.py
python3 scripts/build.py
python3 scripts/geo_match.py
python3 scripts/build_geo.py
python3 scripts/build_persons.py
# ⚠️ build_entities.py 暂停（2026-10-27 事故修复）：data/entities/ 源仅 84 家，
# 而 site/entities/data.json 静态工件有 236 家（其余 152 家产自仓库外管线，同 works）。
# 跑此步会把大库覆盖成小库（已发生并恢复）。源补齐入库后再恢复此行。
# python3 scripts/build_entities.py
python3 scripts/build_today.py

echo "==> 2/2 发布到 netannals 服务器"
rsync -az --delete --delete-excluded --exclude=/data.json site/ netannals:/var/www/net-annals/

echo
echo "✅ 已发布 → https://toolsfox.cn/"
