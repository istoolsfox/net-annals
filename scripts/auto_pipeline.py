#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全自动入库管线（服务器端运行）：拉队列 → 查重 → GLM 初筛 → GLM 成条 → 入库 →
重建站点与 API 库 → git 提交推送 → rsync 上线。
用法:
  python3 scripts/auto_pipeline.py --queue <path>     # API ingest 端点调用
  python3 scripts/auto_pipeline.py --fetch            # 定时模式：ssh 从 n8n 机拉当日队列
纪律：flock 单飞；git pull --ff-only 失败即中止（防覆盖）；commit 前只 add data/events；
     rsync 口径与 deploy.sh 一致（--exclude=/data.json）。crime 桶由 glm_screen 落 note/低分自然排除。"""
import fcntl, glob, json, os, subprocess, sys, time, datetime

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
N8N_SSH = os.environ.get('N8N_SSH', 'toolsfox')
WEBROOT = os.environ.get('WEBROOT', '/var/www/net-annals')


def run(cmd, timeout=None, check=False, **kw):
    """subprocess 封装：argv 列表执行；check=True 时失败即抛（关键步骤用）。"""
    print(f'  $ {cmd if isinstance(cmd, str) else " ".join(cmd)}')
    r = subprocess.run(cmd, shell=isinstance(cmd, str), timeout=timeout, **kw)
    if check and r.returncode != 0:
        raise RuntimeError(f'步骤失败（退出码 {r.returncode}）：{cmd}')
    return r


def main():
    queue = None
    if '--queue' in sys.argv:
        queue = sys.argv[sys.argv.index('--queue') + 1]
    elif '--fetch' in sys.argv:
        stamp = datetime.date.today().isoformat()
        remote = f'/home/node/.n8n/gap/gap_queue_{stamp}.json'
        queue = f'data/derived/gap/gap_queue_{stamp}.json'
        os.makedirs('data/derived/gap', exist_ok=True)
        # n8n 容器在 toolsfox 机：永远跨机 ssh 拉取（toolsfox 免密 sudo）
        r = run(['ssh', '-o', 'ConnectTimeout=15', N8N_SSH,
                 f'sudo docker exec n8n cat {remote}'],
                capture_output=True, timeout=60)
        if r.returncode != 0 or not r.stdout.strip():
            print(f'[{stamp}] 无当日队列，跳过。')
            return 0
        try:
            parsed = json.loads(r.stdout)          # 落盘前验 JSON（防 sudo 配置输出混入）
            assert isinstance(parsed, dict) and isinstance(parsed.get('candidates'), list)
        except Exception:
            print('✗ 拉取内容不是合法队列 JSON，跳过（前 200 字符）：')
            print(r.stdout[:200])
            return 1
        with open(queue, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False)
    else:
        print(__doc__)
        return 2

    lock = open('data/derived/api/pipeline.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('管线已在运行，本次跳过。')
        return 0

    t0 = time.time()
    print(f'=== auto_pipeline {datetime.datetime.now().astimezone().isoformat(timespec="seconds")} queue={queue} ===')

    # 1. 库与远端同步（ff-only 防覆盖；有冲突留给人工）
    if run(['git', 'pull', '--ff-only']).returncode != 0:
        print('✗ git pull 失败（远端有分叉？），中止，队列保留待人工处理。')
        return 1

    # 2. 查重差集
    if run(['python3', 'scripts/batch_gap_queue_diff.py', queue]).returncode != 0:
        return 1

    # 3. GLM 初筛
    if run(['python3', 'scripts/glm_screen.py']).returncode != 0:
        return 1

    # 4. GLM 成条（含 politics；被供应商滤掉的自动留在队列待人工）
    date_tag = datetime.date.today().strftime('%Y%m%d')
    part = f'data/events/.parts/g_gapfinder_{date_tag}.json'
    gw = run(['python3', 'scripts/glm_write.py', '--min-imp', '3', '--all-sens', '--out', part])
    if gw.returncode != 0:
        print('⚠ glm_write 异常退出，本批条目可能不完整（继续重建，队列保留）。')

    # 5. 入库（part 为空则全链只刷新 API 库）
    if os.path.exists(part) and os.path.getsize(part) > 10:
        run(['python3', 'scripts/add_events.py', part])
    else:
        print('  本批无新条（全部查重命中或过滤），只做重建与同步。')

    # 6. 管线 + API 库（关键步骤失败即中止，绝不带病 push/上线）
    run(['python3', 'scripts/normalize.py'], check=True)
    run(['python3', 'scripts/dedup.py'], check=True)
    if run(['python3', 'scripts/build.py'], check=True).returncode != 0:
        return 1
    run(['python3', 'scripts/build_api_db.py'], check=True)
    try:
        run(['python3', '-c',
             'import sys; sys.path.insert(0,"scripts");'
             'import sqlite3; '
             'c=sqlite3.connect("data/derived/api/usage.db"); '
             'c.execute("PRAGMA journal_mode=WAL"); '
             '[c.execute(f"DELETE FROM {t} WHERE day < date(\'now\', \'-45 day\')") '
             'for t in ("key_usage","ip_usage","reg_daily")]; '
             'c.execute("DELETE FROM bans WHERE until < ?",( __import__("time").time(),)); '
             'c.commit()'], check=True)
    except RuntimeError as e:
        print(f'⚠ usage.db 清理失败（不阻塞上线）：{e}')

    # 7. git 提交推送（数据+站点工件一起；.parts 暂存件绝不入库）
    dirty = run(['git', 'status', '--porcelain', '--', 'data/events', 'site'],
                capture_output=True).stdout
    files = [ln[3:].strip() for ln in dirty.splitlines()
             if ln.strip().endswith(('.json', '.gz', '.xml'))
             and '.parts/' not in ln]
    if files:
        run(['git', 'add'] + files)
        commit = run(['git', 'commit', '-m',
                      f'auto: 缺口扫荡入库 {queue.rsplit("/", 1)[-1]}（管线自动批）'],
                     capture_output=True)
        if commit.returncode == 0:
            if run(['git', 'push', 'origin', 'main']).returncode != 0:
                print('✗ git push 失败：站点已本地更新，但远端未同步，需人工检查。')
        else:
            print('  git commit 未产生提交（可能仅时间戳变化），跳过推送。')
    else:
        print('  数据无变化，跳过 commit。')

    # 8. 上线（失败必须体现退出码——评审发现 rsync 半途失败会静默"成功"）
    if run(['rsync', '-az', '--delete', '--delete-excluded', '--exclude=/data.json',
            'site/', f'{WEBROOT}/']).returncode != 0:
        print('✗ rsync 上线失败，需人工检查。')
        return 1

    total = 0
    try:
        for f in glob.glob('data/events/*.json'):
            if '/.' not in f:
                total += len(json.load(open(f, encoding='utf-8')))
    except Exception:
        pass
    print(f'=== 完成 {time.time()-t0:.0f}s 全库 {total} 条 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
