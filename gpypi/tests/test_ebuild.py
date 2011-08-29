#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import unittest2
import tempfile
import shutil

from gpypi import portage_utils
from gpypi.ebuild import *
from gpypi.config import *
from gpypi.tests import *
from gpypi.exc import *


class TestEbuild(BaseTestCase):
    """"""

    def setUp(self):
        # unpacked dir
        self.s = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.s)

        # overlay
        self.overlay_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.overlay_dir)
        profiles = os.path.join(self.overlay_dir, 'profiles')
        os.mkdir(profiles)
        open(os.path.join(profiles, 'repo_name'), 'w').write('gpypi-tests')

        # monkey patch portage environment
        portage_utils.ENV['PORTDIR_OVERLAY'] += ' %s' % self.overlay_dir

        config = ConfigManager(['pypi', 'ini'])
        config.configs['ini'] = dict(overwrite=False, overlay='gpypi-tests', up_pn='foobar', up_pv='1.0')
        self.ebuild = Ebuild(config)
        self.ebuild.unpacked_dir = self.s

    def test_get_dependencies_empty(self):
        self.ebuild.get_dependencies('')
        self.assertEqual(set(), self.ebuild['rdepend'])

    def test_get_dependencies_no_pv(self):
        self.ebuild.get_dependencies('foobar')
        self.assertIn('dev-python/foobar', self.ebuild['rdepend'])

    def test_get_dependencies_eq(self):
        self.ebuild.get_dependencies('foobar==0.1')
        self.assertIn('=dev-python/foobar-0.1', self.ebuild['rdepend'])

    def test_get_dependencies_more_eq(self):
        self.ebuild.get_dependencies('foobar>=0.1')
        self.assertIn('>=dev-python/foobar-0.1', self.ebuild['rdepend'])

    def test_get_dependencies_less_eq(self):
        self.ebuild.get_dependencies('foobar<=0.1')
        self.assertIn('<=dev-python/foobar-0.1', self.ebuild['rdepend'])

    def test_get_dependencies_parse_pv_parse_pn(self):
        self.ebuild.get_dependencies('FooBar==0.1-beta1')
        self.assertIn('=dev-python/foobar-0.1_beta1', self.ebuild['rdepend'])

    def test_get_dependencies_extras(self):
        # test extras
        self.ebuild.get_dependencies('foobar[foo]==0.1')
        self.assertIn('=dev-python/foobar-0.1[foo]', self.ebuild['rdepend'])

    def test_get_dependencies_multi_extras(self):
        self.ebuild.get_dependencies('foobar[foo,bar]==0.1')
        self.assertIn('=dev-python/foobar-0.1[foo,bar]', self.ebuild['rdepend'])

    def test_get_dependencies_if_use(self):
        self.ebuild.get_dependencies('foobar==0.1', 'test')
        self.assertIn('test? ( =dev-python/foobar-0.1 )', self.ebuild['rdepend'])

    def test_get_dependencies_double_less_more1(self):
        self.ebuild.get_dependencies('foobar>=0.1,<0.2')
        self.assertIn('>=dev-python/foobar-0.1', self.ebuild['rdepend'])
        self.assertIn('!<dev-python/foobar-0.2', self.ebuild['rdepend'])

    def test_get_dependencies_double_less_more(self):
        self.ebuild.get_dependencies('foobar<=0.1,>0.2')
        self.assertIn('>dev-python/foobar-0.2', self.ebuild['rdepend'])
        self.assertIn('!<=dev-python/foobar-0.1', self.ebuild['rdepend'])

    def test_get_dependencies_double_more_less(self):
        self.ebuild.get_dependencies('foobar>=0.1,<0.2')
        self.assertIn('>=dev-python/foobar-0.1', self.ebuild['rdepend'])
        self.assertIn('!<dev-python/foobar-0.2', self.ebuild['rdepend'])

    def test_get_dependencies_double_invalid(self):
        self.ebuild.get_dependencies('foobar>=0.1,>0.2')
        self.assertIn('dev-python/foobar', self.ebuild['rdepend'])
        # TODO: test for warning

    def test_get_dependencies_invalid(self):
        self.ebuild.get_dependencies('foobar!=0.2')
        self.assertIn('dev-python/foobar', self.ebuild['rdepend'])
        # TODO: test for warning

    def test_repr(self):
        self.assertIn('<Ebuild', self.ebuild.__repr__())

    def test_add_use(self):
        self.ebuild.add_use('foo')
        self.assertIn('foo', self.ebuild['use'])

    def test_add_inherit(self):
        self.ebuild.add_inherit('foo')
        self.assertIn('foo', self.ebuild['inherit'])

    def test_add_depend(self):
        self.ebuild.add_depend('foo')
        self.assertIn('foo', self.ebuild['depend'])

    def test_add_rdepend(self):
        self.ebuild.add_rdepend('foo')
        self.assertIn('foo', self.ebuild['rdepend'])

    def test_set_metadata_empty(self):
        self.ebuild.set_metadata({})
        self.assertEqual(self.ebuild.metadata, {})

    def test_set_metadata(self):
        self.ebuild.set_metadata({'Home-Page': 'foobar', 'License_': 'GPL'})
        self.assertEqual('foobar', self.ebuild['homepage'])
        self.assertEqual('GPL-2', self.ebuild['license'])

    @unittest2.expectedFailure
    def test_set_ebuild_vars(self):
        ebuild = Ebuild('foobar', '1.0', ['http://blabla.zip'], {})
        self.assertIn('app-arch/unzip', self.ebuild['depend'])

    def test_parse_metadata(self):
        self.ebuild.set_metadata({
            'Home-Page': 'foobar',
            'License_': 'GPL',
            'summary': 'bar',
        })
        self.ebuild.parse_metadata()
        self.assertEqual('foobar', self.ebuild['homepage'])
        self.assertEqual('GPL-2', self.ebuild['license'])
        self.assertEqual('bar', self.ebuild['description'])

    def test_discover_docs(self):
        docs_dir = os.path.join(self.s, 'docs')
        os.mkdir(docs_dir)

        self.ebuild.discover_docs_and_examples()
        self.assertIn('doc', self.ebuild['use'])
        self.assertEqual('docs', self.ebuild['docs_dir'])

    @unittest2.expectedFailure
    def test_discover_sphinx_docs(self):
        self.fail('#')
        # TODO: add support

    def test_discover_examples(self):
        examples_dir = os.path.join(self.s, 'examples')
        os.mkdir(examples_dir)

        self.ebuild.discover_docs_and_examples()
        self.assertIn('examples', self.ebuild['use'])
        self.assertEqual('examples', self.ebuild['examples_dir'])

    def test_discover_nose_tests(self):
        self.ebuild.tests_require = {}
        self.ebuild.setup_keywords['test_suite'] = 'nose.collector'

        self.ebuild.discover_tests()
        self.assertEqual('nosetests', self.ebuild['tests_method'])

    # TODO: assert tests dependencies

    def test_discover_normal_tests(self):
        self.ebuild.tests_require = {}
        tests_dir = os.path.join(self.s, 'tests')
        os.mkdir(tests_dir)

        self.ebuild.discover_tests()
        self.assertEqual('setup.py', self.ebuild['tests_method'])

    ## post_unpack tests

    def test_post_unpack_no_setup_file(self):
        with self.assertRaises(GPyPiNoSetupFile):
            self.ebuild.post_unpack()

    def test_post_unpack_no_unpacked_dir(self):
        self.ebuild.unpacked_dir = '/dev/null/foobar'
        with self.assertRaises(GPyPiNoDistribution):
            self.ebuild.post_unpack()

    def test_post_unpack_most_simple_setup(self):
        setup_file = os.path.join(self.SETUP_SAMPLES_DIR, 'most_simple_setup.tmpl')
        shutil.copy(setup_file, os.path.join(self.s, 'setup.py'))
        self.ebuild.post_unpack()

        self.assertSetEqual(set(), self.ebuild['warnings'])
        self.assertFalse(self.ebuild['python_modname'])
        self.assertEqual(set(['dev-python/setuptools']), self.ebuild['rdepend'])
        self.assertEqual(set(['dev-python/setuptools']), self.ebuild['depend'])
        self.assertEqual(set(), self.ebuild['use'])

    # TODO: ebuild with echo command and no overlay
