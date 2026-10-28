#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 密钥管理：签发/列表/吊销。密钥明文只在签发时展示一次，库内只存 sha256。
用法:
  python3 scripts/api_keys.py issue <名称> ro|admin
  python3 scripts/api_keys.py list
  python3 scripts/api_keys.py revoke <名称>
密钥文件: config/api_keys.json（0600，不入 git）。格式 {"keys":[{"id","key_sha256","role","created"}]}"""
import hashlib, json, os, secrets, sys, datetime

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEY_FILE = os.path.join('config', 'api_keys.json')


def load():
    if os.path.exists(KEY_FILE):
        return json.load(open(KEY_FILE, encoding='utf-8'))
    return {'keys': []}


def save(d):
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    with open(KEY_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.chmod(KEY_FILE, 0o600)


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    d = load()
    if cmd == 'issue' and len(sys.argv) >= 4:
        # issue <名称> <角色> [--quota N] [--contact …]  角色顺序兼容旧用法
        name = sys.argv[2]
        role = sys.argv[3]
        quota = None
        contact = ''
        if '--quota' in sys.argv:
            quota = int(sys.argv[sys.argv.index('--quota') + 1])
        if '--contact' in sys.argv:
            contact = sys.argv[sys.argv.index('--contact') + 1][:120]
        if role == 'public':
            role, quota = 'ro', quota or 2000          # 公开自助领取层：固定 ro+2000/日
        if role not in ('ro', 'admin'):
            print('角色只能是 ro|admin|public')
            return 2
        if any(k['id'] == name for k in d['keys']):
            print(f'名称 {name} 已存在')
            return 2
        raw = 'NA-' + secrets.token_hex(24)
        d['keys'].append({'id': name, 'key_sha256': sha(raw), 'role': role,
                          'daily_quota': quota, 'contact': contact,
                          'created': datetime.datetime.now().astimezone().isoformat(timespec='seconds')})
        save(d)
        print(f'✓ 已签发 {role} 密钥（仅此一次展示，请妥善保存）：\n{raw}')
    elif cmd == 'list':
        for k in d['keys']:
            print(f"{k['id']:20s} {k['role']:6s} {k['created'][:10]} sha:{k['key_sha256'][:12]}…")
    elif cmd == 'revoke' and len(sys.argv) == 3:
        n = len(d['keys'])
        d['keys'] = [k for k in d['keys'] if k['id'] != sys.argv[2]]
        save(d)
        print(f"吊销 {n - len(d['keys'])} 把")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
