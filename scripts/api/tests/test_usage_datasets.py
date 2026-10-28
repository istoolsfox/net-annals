# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api import config, datasets, usage_store  # noqa: E402


class TestUsageStore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._old = config.USAGE_DB
        config.USAGE_DB = os.path.join(self.dir, 'usage.db')
        usage_store._conn = None

    def tearDown(self):
        config.USAGE_DB = self._old
        usage_store._conn = None

    def test_bump_counts(self):
        self.assertEqual(usage_store.bump('ip_usage', 'ip', '2026-10-26', '1.1.1.1'), 1)
        self.assertEqual(usage_store.bump('ip_usage', 'ip', '2026-10-26', '1.1.1.1'), 2)
        self.assertEqual(usage_store.bump('ip_usage', 'ip', '2026-10-26', '2.2.2.2'), 1)
        self.assertEqual(usage_store.bump('ip_usage', 'ip', '2026-10-27', '1.1.1.1'), 1)

    def test_ban_roundtrip(self):
        usage_store.ban('3.3.3.3', 1, 'test')
        b = usage_store.banned_since('3.3.3.3')
        self.assertIsNotNone(b)
        self.assertEqual(b[1], 'test')
        # 未过期封禁 prune 不清；过期（until 已过）后被清且视为未封禁
        with usage_store._lock:
            usage_store.conn().execute("UPDATE bans SET until=0 WHERE ip='3.3.3.3'")
            usage_store.conn().commit()
        self.assertIsNone(usage_store.banned_since('3.3.3.3'))
        usage_store.prune(days=45)
        with usage_store._lock:
            n = usage_store.conn().execute('SELECT COUNT(*) c FROM bans').fetchone()['c']
        self.assertEqual(n, 0)

    def test_banned_fail_open_on_db_error(self):
        # USAGE_DB 的父路径是一个已存在的【文件】→ connect 真抛 OperationalError → fail-open 返回 None
        blocker = os.path.join(self.dir, 'blocker')
        with open(blocker, 'w') as fh:
            fh.write('x')
        config.USAGE_DB = os.path.join(blocker, 'usage.db')
        usage_store._conn = None
        try:
            self.assertIsNone(usage_store.banned_since('4.4.4.4'))
            self.assertIsNone(usage_store.peek('ip_usage', 'ip', '2026-10-28', '4.4.4.4'))
            self.assertIsNone(usage_store.bump('ip_usage', 'ip', '2026-10-28', '4.4.4.4'))
        finally:
            config.USAGE_DB = os.path.join(self.dir, 'usage.db')
            usage_store._conn = None


class TestDatasets(unittest.TestCase):
    def test_registry_shape(self):
        for ds, spec in datasets.DATASETS.items():
            self.assertIn('label', spec)
            for param, col in spec['filters'].items():
                self.assertIn(col, ('kind', 'region', 'year'), f'{ds}.{param}')

    def test_validate_filter(self):
        self.assertEqual(datasets.validate_filter('cn', 'region'), 'cn')
        self.assertIsNone(datasets.validate_filter('mars', 'region'))
        self.assertEqual(datasets.validate_filter('1985', 'year'), 1985)
        self.assertIsNone(datasets.validate_filter('19x0', 'year'))
        self.assertEqual(datasets.validate_filter('company', 'kind'), 'company')
        self.assertIsNone(datasets.validate_filter('a;b', 'kind'))


if __name__ == '__main__':
    unittest.main()
