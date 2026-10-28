# public-apis PR 素材包（备案通过后使用）

目标仓库：[public-apis/public-apis](https://github.com/public-apis/public-apis)（GitHub 上最大的免费 API 目录）。
**触发条件：toolsfox.cn 解析恢复且 `https://toolsfox.cn/api/v1/health` 公网可达**（每日 9 点自动监控会通知）。

## 前置检查（提交前过一遍）

```bash
dig +short toolsfox.cn A            # 有 A 记录
curl -s https://toolsfox.cn/api/v1/ | python3 -m json.tool   # 根索引 200
curl -s "https://toolsfox.cn/api/v1/search?q=互联网"          # 中文检索正常
curl -sI -H "Origin: https://example.com" https://toolsfox.cn/api/v1/meta | grep -i access-control  # CORS 头在
```

提交 PR 前把 `docs/API.md` 顶部「⚠️ 临时状态（备案期）」横幅删掉（PR 评审员会点文档链接）。

## README 行（5 列，插入 Open Data 小节，按字母序找 C 位置）

```markdown
| [China Internet Chronicle](https://toolsfox.cn/api/v1/) | Timeline API of China & the world since 1970: 6,000+ sourced events, people & works (Chinese) | No | Yes | Yes |
```

描述实测 95 字符（上限 100）✓；Auth 值 `No` 合规；名称不含 TLD、不以 API 结尾 ✓。
若评审认为 Open Data 不合适，备选小节：**Events**。

## PR 标题 / 提交信息

- PR 标题：`Add China Internet Chronicle API`
- Commit message：`Add China Internet Chronicle API to Open Data`
- 规则：目标 `master` 分支；squash 成单提交；一个 PR 只加一个 API；先搜历史 PR 确认无重复。

## PR 正文（复制即用）

```markdown
Adds **China Internet Chronicle** to the **Open Data** section (alphabetical under C).

**What it is:** A strictly read-only timeline API covering China and the world since 1970 —
6,134 historically sourced events with exact dates, categories, tags, impact notes and citation
URLs — plus four extra datasets: persons (382), entities/companies (236), works (159) and
group biographies (78). Content is in Chinese; identifiers and `en_name` fields are English.

**Highlights**
- HTTPS ✓, CORS ✓ (`Access-Control-Allow-Origin: *` on all JSON responses), no auth required
- Anonymous tier: 200 req/day/IP, 20 req/min; free API key (self-service, no signup):
  2,000 req/day via `POST /keys/register`
- Filters: year, date range, category, region, layer, full-text `q` (multi-word AND,
  CJK substring match), relevance-scored `/search`
- Errors are a uniform `{"error": "..."}` contract; ETag/304 supported; 429 carries `Retry-After`
- There are no write endpoints — data enters via reviewed GitHub PRs only

**Example**
```bash
curl "https://toolsfox.cn/api/v1/search?q=互联网"
curl "https://toolsfox.cn/api/v1/persons?field=scientist&limit=10"
```

**Docs:** https://github.com/istoolsfox/net-annals/blob/main/docs/API.md
**Self-describing index:** https://toolsfox.cn/api/v1/
**License:** data under CC BY-NC 4.0-equivalent terms (attribution, non-commercial).
```

## 评审员视角自检

- [ ] 根索引 `/api/v1/` 打开即见端点清单（已实现，就是为这个 PR 加的落地页）
- [ ] 文档链接直达 GitHub docs/API.md（公开仓库）
- [ ] HTTPS 证书有效（Let's Encrypt 自动续期）
- [ ] 匿名即可完成上述全部 example（无需 key）
- [ ] 描述 ≤100 字符、字母序插入、无 TLD、名称不以 API 结尾
