#!/usr/bin/env bash
# 校验合并编年史数据 → site/data.json
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build.py
echo
echo "预览站点： cd site && python3 -m http.server 8788  →  http://localhost:8788"
