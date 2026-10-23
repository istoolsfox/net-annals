#!/usr/bin/env python3
"""生成 OG 分享卡 site/assets/og-card.png（1200×630）。用法：python3 scripts/make_og.py"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 630
BG = (18, 21, 29)
TEXT = (238, 236, 230)
DIM = (150, 150, 158)
ACCENT = (201, 168, 106)
LINE = (52, 56, 68)

FONT_TTC = "/System/Library/Fonts/Supplemental/Songti.ttc"


def font(size, index=4):
    return ImageFont.truetype(FONT_TTC, size, index=index)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# 顶部时代线：1972—2026 的时间轴 + 节点
y_axis = 108
d.line([(80, y_axis), (W - 80, y_axis)], fill=LINE, width=2)
milestones = [(1972, 0.0), (1987, 0.24), (1994, 0.40), (2003, 0.60), (2012, 0.78), (2026, 1.0)]
for year, t in milestones:
    x = 80 + t * (W - 160)
    big = year in (1987, 1994, 2026)
    r = 7 if big else 4
    d.ellipse([x - r, y_axis - r, x + r, y_axis + r], fill=ACCENT if big else LINE)
    d.text((x, y_axis + 16), str(year), font=font(22, 4), fill=DIM, anchor="ma")

# 主标题
d.text((80, 190), "互联网编年史", font=font(124), fill=TEXT)
# 副标题
d.text((84, 360), "1972 — 2026 · 精确到日 · 每条可溯源", font=font(44, 4), fill=DIM)
# 三栏口号
d.text((84, 452), "世家志 · 兴衰史        人物志 · 人生历程        历史上的今天", font=font(34, 4), fill=ACCENT)
# 底部 URL
d.text((84, 548), "toolsfox.top/net-annals", font=font(30, 4), fill=DIM)

out = os.path.join(ROOT, "site", "assets", "og-card.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out, "PNG")
print(f"✓ OG 卡已生成 {out}（{os.path.getsize(out) // 1024}KB）")
