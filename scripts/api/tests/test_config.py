# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api import config  # noqa: E402


class TestLayerOf(unittest.TestCase):
    def test_legacy_range_files(self):
        self.assertEqual(config.layer_of('data/events/1972-1985.json'), '')
        self.assertEqual(config.layer_of('data/events/2000-2004-games.json'), 'games')
        self.assertEqual(config.layer_of('data/events/1970-2026-disasters.json'), 'disasters')
        self.assertEqual(config.layer_of('data/events/1994-2026-games2.json'), 'games2')
        self.assertEqual(config.layer_of('data/events/2005-2009-tech.json'), 'tech')

    def test_single_date_contrib_file(self):
        self.assertEqual(config.layer_of('data/events/1994-04-20-tech-china-net.json'), 'tech')
        self.assertEqual(config.layer_of('data/events/1986-09-14-china-study-society.json'), '')

    def test_unknown_layer_falls_back_to_main(self):
        # 绝不编造层码：识别不了归主时间线
        self.assertEqual(config.layer_of('data/events/1994-04-20-foobar-x.json'), '')


class TestRegexes(unittest.TestCase):
    def test_id(self):
        self.assertTrue(config.RE_ID.fullmatch('1994-04-20-china-internet'))
        self.assertFalse(config.RE_ID.fullmatch('1994-4-20-x'))
        self.assertFalse(config.RE_ID.fullmatch('1994-04-20-大写'))
        self.assertFalse(config.RE_ID.fullmatch('1994-04-20--x'))

    def test_key_shape(self):
        self.assertTrue(config.RE_KEY.fullmatch('NA-' + 'a' * 48))
        self.assertFalse(config.RE_KEY.fullmatch('NA-' + 'a' * 47))

    def test_sorts_whitelist(self):
        self.assertNotIn('1;DROP TABLE events', config.SORTS)


if __name__ == '__main__':
    unittest.main()
