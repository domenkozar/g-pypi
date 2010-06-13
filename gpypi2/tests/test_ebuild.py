#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import unittest2

from gpypi2.ebuild import *
from gpypi2.tests import *


class TestEbuild(BaseTestCase):
    """"""

    def test_get_dependencies(self):
        ebuild_args = ('foobar', '1.0', '')

        # empty
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('')
        self.assertEqual(set(), ebuild['rdepend'])

        # test no pv
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('foobar')
        self.assertIn('dev-python/foobar', ebuild['rdepend'])

        # test ==
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('foobar==0.1')
        self.assertIn('=dev-python/foobar-0.1', ebuild['rdepend'])

        # test >=
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('foobar>=0.1')
        self.assertIn('>=dev-python/foobar-0.1', ebuild['rdepend'])

        # test <=
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('foobar<=0.1')
        self.assertIn('<=dev-python/foobar-0.1', ebuild['rdepend'])

        # test parse_pv and parse_pn
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('FooBar==0.1-beta1')
        self.assertIn('=dev-python/foobar-0.1_beta1', ebuild['rdepend'])

        # test extras
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('foobar[foo]==0.1')
        self.assertIn('=dev-python/foobar-0.1[foo]', ebuild['rdepend'])

        # test multiple extras
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('foobar[foo,bar]==0.1')
        self.assertIn('=dev-python/foobar-0.1[foo,bar]', ebuild['rdepend'])

        # test if_use
        ebuild = Ebuild(*ebuild_args)
        ebuild.get_dependencies('foobar==0.1', 'test')
        self.assertIn('test? =dev-python/foobar-0.1', ebuild['rdepend'])

        # TODO: tests for double operators (with extras and if_uses)

    def test_ebuild_repr(self):
        out = Ebuild('foobar', '1.0', '').__repr__()
        self.assertIn('<Ebuild', out)
