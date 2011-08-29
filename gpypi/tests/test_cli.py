#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import unittest2
import mock
from pkg_resources import parse_requirements

from gpypi.cli import *
from gpypi.tests import *


class TestGPyPI(BaseTestCase):
    """"""

    def setUp(self):
        class Options:
            no_deps = False
            overwrite = False
            category = False
            uri = None

        self.gpypi = GPyPI('foobar', '1.0', Options())
        self.packages = []
        def side_effect():
            self.packages.append([self.gpypi.package_name, self.gpypi.version])
            return mock.DEFAULT
        self.do_ebuild_side_effect = side_effect

    def test_create_ebuild_with_deps(self):
        """"""

        returns = parse_requirements(['sphinx==0.6', 'foobar2>=1.0'])
        patched_do_ebuild = mock.Mock(return_value=returns, side_effect=self.do_ebuild_side_effect)

        with mock.patch.object(self.gpypi, 'do_ebuild', patched_do_ebuild):
            self.gpypi.create_ebuilds()

        self.assertEqual([['foobar', '1.0'], ['sphinx', None], ['foobar2', None]], self.packages)


class TestCLI(BaseTestCase):
    """"""



class TestMain(BaseTestCase):
    """"""

    def test_help(self):
        """docstring for test_help"""
        self.assertRaises(SystemExit, main, ['--help'])
