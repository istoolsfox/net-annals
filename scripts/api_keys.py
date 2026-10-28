#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 密钥管理 CLI：签发/列表/吊销。密钥明文只在签发时展示一次，库内只存 sha256。
用法:
  python3 scripts/api_keys.py issue <名称> ro|admin|public [--quota N] [--contact …]
  python3 scripts/api_keys.py list
  python3 scripts/api_keys.py revoke <名称>
密钥文件: config/api_keys.json（0600，不入 git）。
存储/原子写实现在 scripts/api/keys_store.py，与服务端共用同一份。"""
import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'scripts')
from api import keys_store


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == 'issue' and len(sys.argv) >= 4:
        # issue <名称> <角色> [--quota N] [--contact …]  角色顺序兼容旧用法
        name, role = sys.argv[2], sys.argv[3]
        quota, contact = None, ''
        try:
            if '--quota' in sys.argv:
                quota = int(sys.argv[sys.argv.index('--quota') + 1])
            if '--contact' in sys.argv:
                contact = sys.argv[sys.argv.index('--contact') + 1][:120]
        except (IndexError, ValueError):
            print('--quota/--contact 缺少参数值')
            return 2
        try:
            raw = keys_store.issue(name, role, quota=quota, contact=contact)
        except ValueError as e:
            print(f'✗ {e}')
            return 2
        print(f'✓ 已签发 {role} 密钥（仅此一次展示，请妥善保存）：\n{raw}')
    elif cmd == 'list':
        for k in keys_store.list_keys():
            print(f"{k['id']:20s} {k['role']:6s} "
                  f"{str(k.get('daily_quota') or '∞'):>6s} {k['created'][:10]} "
                  f"sha:{k['key_sha256'][:12]}…")
    elif cmd == 'revoke' and len(sys.argv) == 3:
        n = keys_store.revoke(sys.argv[2])
        print(f'吊销 {n} 把')
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
