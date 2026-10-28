# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api import keys_store  # noqa: E402


class TestKeysStore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.kf = os.path.join(self.dir, 'keys.json')
        self.lock = os.path.join(self.dir, 'keys.lock')
        self._old_lock = keys_store.config.KEY_LOCK
        keys_store.config.KEY_LOCK = self.lock
        keys_store._cache['mtime'] = 0
        keys_store._cache['map'] = {}

    def tearDown(self):
        keys_store.config.KEY_LOCK = self._old_lock

    def test_issue_find_revoke(self):
        raw = keys_store.issue('t1', 'ro', quota=100, path=self.kf)
        self.assertTrue(raw.startswith('NA-'))
        self.assertIsNone(keys_store.find('NA-' + '0' * 48, path=self.kf))
        k = keys_store.find(raw, path=self.kf)
        self.assertIsNotNone(k)
        self.assertEqual(k['role'], 'ro')
        self.assertEqual(k['daily_quota'], 100)
        self.assertEqual(keys_store.revoke('t1', path=self.kf), 1)
        self.assertIsNone(keys_store.find(raw, path=self.kf))

    def test_public_role_maps_to_ro_default_quota(self):
        raw = keys_store.issue('t2', 'public', path=self.kf)
        k = keys_store.find(raw, path=self.kf)
        self.assertEqual(k['role'], 'ro')
        self.assertEqual(k['daily_quota'], keys_store.config.DEFAULT_RO_QUOTA)

    def test_dup_name_gets_suffix(self):
        r1 = keys_store.issue('dup', 'ro', path=self.kf)
        r2 = keys_store.issue('dup', 'ro', path=self.kf)
        self.assertNotEqual(r1, r2)
        self.assertEqual(len(keys_store.list_keys(self.kf)), 2)

    def test_bad_role(self):
        with self.assertRaises(ValueError):
            keys_store.issue('t3', 'god', path=self.kf)

    def test_plaintext_not_stored(self):
        import json
        raw = keys_store.issue('t4', 'ro', path=self.kf)
        with open(self.kf, encoding='utf-8') as f:
            self.assertNotIn(raw, f.read())


if __name__ == '__main__':
    unittest.main()
