#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import os
import tempfile
import shutil
import logging

import mock
import argparse

from gpypi.config import *
from gpypi.tests import *
from gpypi.exc import *


class TestConfig(BaseTestCase):
    """"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir)

    def test_repr(self):
        config = Config.from_setup_py({'overlay': 'foobar'})
        self.assertEqual("<Config {'overlay': 'foobar'}>", config.__repr__())

    def test_from_pypyi(self):
        c = Config.from_pypi({'overlay': 'foobar'})
        self.assertEqual('foobar', c['overlay'])

    def test_from_setup_py(self):
        c = Config.from_setup_py({'overlay': 'foobar'})
        self.assertEqual('foobar', c['overlay'])

    def test_from_ini(self):
        ini_path = os.path.join(self.tmp_dir, 'ini')
        f = open(ini_path, 'w')
        f.write("""
[config]
overlay = local
category = dev-python
        """)
        f.close()

        c = Config.from_ini(ini_path)
        self.assertEqual('local', c['overlay'])
        self.assertEqual('dev-python', c['category'])

    def test_from_argparse(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', action='store', dest='overlay')
        args = parser.parse_args(['-v', 'foobar'])
        c = Config.from_argparse(args)

        self.assertEqual('foobar', c['overlay'])

    def test_validate_bool(self):
        self.assertEqual(True, Config.validate('overwrite', 'y'))
        self.assertRaises(GPyPiValidationError, Config.validate, 'overwrite', 'foobar')

    def test_validate_str(self):
        self.assertEqual(u'foobar', Config.validate('uri', 'foobar'))
        self.assertEqual(u'foobar', Config.validate('uri', u'foobar'))
        self.assertRaises(GPyPiValidationError, Config.validate, 'uri', True)


class TestConfigManager(BaseTestCase):
    """"""

    def setUp(self):
        self.mgr = ConfigManager(['pypi', 'setup_py'], ['category'])
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir)

    def test_order(self):
        self.mgr.configs['pypi'] = Config.from_pypi({})
        self.mgr.configs['setup_py'] = Config.from_setup_py({'overlay': 'bar'})

        self.assertEqual('bar', self.mgr.overlay)

        self.mgr.use = ['setup_py', 'pypi']
        self.mgr.configs['setup_py'] = Config.from_pypi({'overlay': 'bar'})
        self.mgr.configs['pypi'] = Config.from_pypi({})

        self.assertEqual('bar', self.mgr.overlay)

    def test_empty_default(self):
        self.mgr.configs['pypi'] = Config.from_pypi({})
        self.mgr.configs['setup_py'] = Config.from_setup_py({})

        self.assertEqual(Config.allowed_options['overlay'][2], self.mgr.overlay)

    @mock.patch('gpypi.config.Questionnaire')
    def test_use_questionaire(self, q):
        self.mgr = ConfigManager(['pypi', 'setup_py'], ['category'], q)
        self.mgr.configs['pypi'] = Config.from_pypi({})
        self.mgr.category

        self.assertEqual([('ask', ('category',), {})], self.mgr.q.method_calls)
        self.assertEqual(1, self.mgr.q.ask.call_count)

    @mock.patch('gpypi.config.Questionnaire')
    def test_use_questionaire_multiple_times(self, q):
        self.mgr = ConfigManager(['pypi', 'setup_py'], ['category'], q)
        self.mgr.configs['pypi'] = Config.from_pypi({})
        self.mgr.category

        self.assertEqual([('ask', ('category',), {})], self.mgr.q.method_calls)
        self.assertEqual(1, self.mgr.q.ask.call_count)

        self.mgr.category
        self.assertEqual([('ask', ('category',), {})], self.mgr.q.method_calls)
        self.assertEqual(1, self.mgr.q.ask.call_count)

    def test_non_existent_option(self):
        self.mgr.configs['pypi'] = Config.from_pypi({})

        self.assertRaises(GPyPiConfigurationError, lambda: self.mgr.foobar)

    def test_no_config_file(self):
        self.assertRaises(GPyPiConfigurationError, lambda: self.mgr.overlay)

    def test_is_use_unique(self):
        self.assertRaises(GPyPiConfigurationError, ConfigManager,
            ['pypi', 'pypi', 'setup_py'])

    def test_load_from_ini(self):
        ini_path = os.path.join(self.tmp_dir, 'ini')
        f = open(ini_path, 'w')
        f.write("""
[config]

[config_manager]
use = argparse pypi ini setup_py
questionnaire_options = overlay uri package version
        """)
        f.close()

        self.assertTrue(os.path.exists(ini_path))
        mgr = ConfigManager.load_from_ini(ini_path)
        self.assertTrue(os.path.exists(ini_path))

        self.assertEqual(mgr.use, ['questionnaire', 'argparse', 'pypi', 'ini', 'setup_py'])
        self.assertEqual(mgr.questionnaire_options, ['overlay', 'uri', 'package', 'version'])

    def test_create_ini(self):
        ini_path = os.path.join(self.tmp_dir, 'ini')
        self.assertFalse(os.path.exists(ini_path))
        ConfigManager.load_from_ini(ini_path)
        self.assertTrue(os.path.exists(ini_path))

    def test_empty_ini(self):
        ini_path = os.path.join(self.tmp_dir, 'ini')
        open(ini_path, 'w')
        self.assertTrue(os.path.exists(ini_path))
        ConfigManager.load_from_ini(ini_path)
        self.assertTrue(os.path.exists(ini_path))

    def test_load_from_ini_source(self):
        ini_path = os.path.join(self.tmp_dir, 'ini')
        f = open(ini_path, 'w')
        f.write("""
[config]
overlay = local
category = dev-python

[config_manager]
use = ini pypi setup_py argparse
questionnaire_options = overlay
        """)
        f.close()

        mgr = ConfigManager.load_from_ini(ini_path)
        self.assertEqual(2, len(mgr.configs['ini']))
        self.assertEqual('local', mgr.overlay)

class TestQuestionnaire(BaseTestCase):
    """"""

    def setUp(self):
        self.handler = ListHandler()
        logging.getLogger().addHandler(self.handler)
        config = ConfigManager(['ini'])
        config.configs['ini'] = {}
        self.q = Questionnaire(config)

    def test_ask(self):
        self.assertEqual(u'foobar', self.q.ask('overlay', lambda x: 'foobar'))

    def test_print_help(self):
        self.assertEqual(0, len(self.handler.info))
        self.q.ask('overlay', lambda x: 'foobar')
        self.assertEqual(3, len(self.handler.info))
        self.q.ask('overlay', lambda x: 'foobar')
        self.assertEqual(3, len(self.handler.info))

    def test_error_handling(self):
        answer = iter(['foobar', 'y'])
        self.assertEqual(True, self.q.ask('no_deps', lambda x: answer.next()))
        self.assertTrue('Not a boolean' in self.handler.error[0])
        self.assertTrue('foobar' in self.handler.error[0])

    def test_use_default(self):
        self.assertEqual(u'none', self.q.ask('format', lambda x: ''))
