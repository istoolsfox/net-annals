# SERVER · toolsfox.cn 服务器运行手册

> 2026-10-23 迁移自 toolsfox 服务器（旧站对 /net-annals 路径 301 过渡）。
> 本文件是新服务器唯一运行真相源，改配置必须同步改这里。

## 一、服务器档案

| 项 | 值 |
|---|---|
| 主机 | 阿里云 ECS `118.178.238.120`（SSH 别名 `netannals`，用户 toolsfox_netannals，免密 sudo） |
| 系统 | Ubuntu 24.04.5 · 2C / 1.7G RAM / 40G 盘 |
| 域名 | **toolsfox.cn** + www（阿里云 DNS，A 记录 TTL 600；本机 `aliyun` CLI 可直接增改解析） |
| 证书 | Let's Encrypt（certbot --nginx 自动续期配置已装） |
| 站点根 | `/var/www/net-annals/`（属主 toolsfox_netannals） |

## 二、已部署的防护栈

- **nginx**：server_tokens off；单 IP 限流 20r/s（burst 40）+ 并发连接 ≤30；`/.git /.env 等`与备份后缀直接 444 断连；安全头五件套（nosniff/XFO/Referrer-Policy/HSTS 30d/Permissions-Policy）；缓存策略=带版本静态资源 30d immutable、数据 json/gz 5min。
- **ufw**：仅 22/80/443。
- **fail2ban**：sshd（5 次失败封 1h）+ nginx-limit-req（60s 内 20 次限流触发封 10m）。
- **内核**：syncookies/somaxconn 4096/rp_filter 等（`/etc/sysctl.d/99-netannals.conf`）。

## 三、发布

```bash
# 仓库内一键（构建全部栏目数据 → rsync 到 netannals）
./scripts/deploy.sh
# 回滚（老服务器仍在，301 已开；撤回 301 见下节）
rsync -az --delete --exclude=/data.json site/ toolsfox:/var/www/net-annals/
```

## 四、⚠️ ICP 备案（未完成，最高优先级）

阿里云对未备案域名的 **80 端口**返回 `Non-compliance ICP Filing` 拦截页（Server: Beaver），
443 暂不受影响但阿里云保留进一步处置权。**需要站长在阿里云控制台提交个人备案**（1-2 周）。
备案通过前，Let's Encrypt 的 HTTP-01 验证（80 端口）不可用。

## 五、证书续期（备案通过前的预案）

现证书到期 **2027-01-21**。若到期前备案未通过，HTTP-01 续期会被 80 端口拦截，改走 DNS-01：

```bash
# 本机（有 aliyun CLI 凭证）为服务器签发，两条 TXT 由 API 自动添删
ssh netannals 'sudo certbot certonly --manual --preferred-challenges dns -d toolsfox.cn -d www.toolsfox.cn'
# 按提示在本机执行：
aliyun alidns AddDomainRecord --DomainName toolsfox.cn --RR "_acme-challenge" --Type TXT --Value "<提示的值>"
# 验证生效后回车继续；完成后删除 TXT 记录
```
到期前 30 天自动化会提醒（见 CronCreate：toolsfox.cn 证书到期检查）。

## 六、常用运维命令

```bash
ssh netannals 'sudo fail2ban-client status nginx-limit-req'   # 看限流封禁名单
ssh netannals 'sudo fail2ban-client unbanip <IP>'             # 解封（自家 IP 误封）
ssh netannals 'sudo tail -50 /var/log/nginx/net-annals.error.log'
ssh netannals 'uptime; free -h'                               # 负载速查
```

## 七、已知问题台账

- [ ] ICP 备案未办（80 被拦，见第四节）——**站长行动项**
- [ ] LibreSSL 系客户端（macOS 系统 curl/python3）TLS 握手被 RST，OpenSSL 3.x/浏览器正常——疑似边缘组件指纹策略，待观察；影响面为部分命令行工具
- [ ] CSP 未启用（全站内联脚本，启用需改造，暂缓）
- [ ] 老服务器（toolsfox.top）301 过渡期保留；2027 年可下线
