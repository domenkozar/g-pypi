#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import os 
import tempfile
import shutil
import logging

import mock

from gpypi2.config import *
from gpypi2.tests import *
from gpypi2.exc import *


class TestConfig(BaseTestCase):
    """"""

    def test_repr(self):
        config = Config.from_setup_py({'overlay': 'foobar'})
        self.assertEqual("<Config {'overlay': 'foobar'}>", config.__repr__())

    def test_from_pypyi(self):
        pass

    def test_from_ini(self):
        pass

    def test_from_argparse(self):
        pass

    def test_from_setup_py(self):
        pass

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

    @mock.patch('gpypi2.config.Questionnaire')
    def test_use_questionaire(self, q):
        self.mgr = ConfigManager(['pypi', 'setup_py'], ['category'], q)
        self.mgr.configs['pypi'] = Config.from_pypi({})
        self.mgr.category

        self.assertEqual([('ask', ('category',), {})], self.mgr.q.method_calls)

    def test_non_existent_option(self):
        self.mgr.configs['pypi'] = Config.from_pypi({})

        self.assertRaises(GPyPiConfigurationError, lambda: self.mgr.foobar)

    def test_no_config_file(self):
        self.assertRaises(GPyPiConfigurationError, lambda: self.mgr.overlay)

    def test_is_use_unique(self):
        self.assertRaises(GPyPiConfigurationError, ConfigManager,
            ['pypi', 'pypi', 'setup_py'])

    def test_load(self):
        ini_path = os.path.join(self.tmp_dir, 'ini')

        self.assertFalse(os.path.exists(ini_path))
        mgr = ConfigManager.load_from_ini(ini_path)
        self.assertTrue(os.path.exists(ini_path))

        self.assertEqual(mgr.use, ['pypi', 'ini', 'setup_py', 'argparse'])
        self.assertEqual(mgr.questionnaire_options, ['overlay'])


class TestQuestionnaire(BaseTestCase):
    """"""

    def setUp(self):
        self.handler = ListHandler()
        logging.getLogger().addHandler(self.handler)
        self.q = Questionnaire()

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
