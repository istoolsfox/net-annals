#!/usr/bin/env python3
"""Agent 产出归一化：把子 Agent 常见的格式偏差修到门禁标准。
- region: china → cn
- date_confidence: reported/estimated → single-source/uncertain
- date: month/year 精度归一到 01 日；id 前缀与 date 对齐、转小写
"""
import json
import sys
from datetime import date
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "data" / "events"
CONF_MAP = {"reported": "single-source", "estimated": "uncertain", "media": "single-source"}

def main() -> int:
    changed = 0
    for f in sorted(EV.glob("*.json")):
        if f.name.startswith("."):
            continue  # agent 备份/分片不参与归一化
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"✗ {f.name}: JSON 解析失败（可能正在写入），跳过 —— {exc}")
            continue
        dirty = False
        for e in d:
            if e.get("region") == "china":
                e["region"] = "cn"; dirty = True
            if not isinstance(e.get("milestone"), bool):  # 缺失/畸形 milestone 兜底
                e["milestone"] = False; dirty = True
            c = e.get("date_confidence")
            if c in CONF_MAP:
                e["date_confidence"] = CONF_MAP[c]; dirty = True
            # 宽松修复畸形日期（如 1990-1001 / 19901001）
            raw = e.get("date", "")
            digits = raw.replace("-", "")
            if len(digits) == 8 and digits.isdigit():
                try:
                    date(int(digits[:4]), int(digits[4:6]), int(digits[6:]))
                    fixed = f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
                    if fixed != raw:
                        e["date"] = fixed; dirty = True
                except ValueError:
                    pass
            acc = e.get("date_accuracy")
            if acc == "month" and not e["date"].endswith("01"):
                e["date"] = e["date"][:8] + "01"; dirty = True
            if acc == "year" and not e["date"].endswith("01-01"):
                e["date"] = e["date"][:5] + "01-01"; dirty = True
            if not e["id"].startswith(e["date"]):
                slug = re.sub(r"^\d{4}-?\d{0,2}-?\d{0,2}-?", "", e["id"]).strip("-")
                e["id"] = e["date"] + "-" + (slug or "event"); dirty = True
            if "." in e["id"]:  # 版本号里的点号不合 slug 规范
                e["id"] = e["id"].replace(".", "-"); dirty = True
            if e["id"] != e["id"].lower():
                e["id"] = e["id"].lower(); dirty = True
        if dirty:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=0), encoding="utf-8")
            changed += 1
            print(f"✓ {f.name} 归一化（{len(d)} 条）")
    print(f"完成，改动 {changed} 个文件")
    return 0

if __name__ == "__main__":
    sys.exit(main())
