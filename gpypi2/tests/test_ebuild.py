#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import unittest2

from gpypi2.ebuild import *
from gpypi2.tests import *


class TestEbuild(BaseTestCase):
    """"""

    def setUp(self):
        self.ebuild_args = ('foobar', '1.0', '', {})
        self.ebuild = Ebuild(*self.ebuild_args)

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
        self.assertIn('test? =dev-python/foobar-0.1', self.ebuild['rdepend'])

        # TODO: tests for double operators (with extras and if_uses)

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

