#!/usr/bin/env bash
# 一键发布（服务器副本同步）：构建校验 → rsync 到 netannals 服务器
# ⚠️ 2026-11-02 起对外主站 = GitHub Pages（https://istoolsfox.github.io/net-annals/）。
#    本脚本只刷新服务器副本（toolsfox.cn 已退役，不对外服务）；对外发布请跑 scripts/deploy_pages.sh。
# 服务器直出回滚方式（若恢复备案/换域名）：rsync site/ netannals:/var/www/net-annals/
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
echo "✅ 服务器副本已更新（对外主站为 GitHub Pages，对外发布请跑 scripts/deploy_pages.sh）"
