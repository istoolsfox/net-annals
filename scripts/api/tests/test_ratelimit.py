# -*- coding: utf-8 -*-
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api import ratelimit  # noqa: E402


class TestBurst(unittest.TestCase):
    def setUp(self):
        ratelimit._hits.clear()
        ratelimit._probes.clear()

    def test_under_limit_ok(self):
        for _ in range(19):
            ratelimit.burst('ip:1.2.3.4', 20)

    def test_over_limit_raises(self):
        with self.assertRaises(ratelimit.RateLimited):
            for _ in range(21):
                ratelimit.burst('ip:1.2.3.4', 20)

    def test_window_expiry(self):
        ratelimit.burst('ip:5.6.7.8', 1)
        with self.assertRaises(ratelimit.RateLimited):
            ratelimit.burst('ip:5.6.7.8', 1)
        with mock.patch('api.ratelimit.time.time', return_value=__import__('time').time() + 61):
            ratelimit.burst('ip:5.6.7.8', 1)   # 旧记录滑出窗口后放行

    def test_subjects_isolated(self):
        ratelimit.burst('key:a', 1)
        ratelimit.burst('key:b', 1)   # 不同主体互不影响


class TestProbe(unittest.TestCase):
    def setUp(self):
        ratelimit._probes.clear()

    def test_threshold(self):
        for _ in range(19):
            self.assertFalse(ratelimit.record_probe('9.9.9.9'))
        self.assertTrue(ratelimit.record_probe('9.9.9.9'))
        self.assertFalse(ratelimit.record_probe('8.8.8.8'))   # 其他 IP 独立计数


if __name__ == '__main__':
    unittest.main()
