#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import gpypi
from gpypi.utils import *
from gpypi.tests import *
from gpypi.tests import test_ebuild

import mocker


class TestUtils(BaseTestCase):
    """Unittests for utilities"""
    HERE = os.path.dirname(os.path.abspath(__file__))

    def test_import_path(self):
        module = import_path(os.path.join(self.HERE, 'test_ebuild.py'))
        self.assertTrue(module.TestEbuild)

    def test_asbool(self):
        self.assertTrue(asbool('y'))
        self.assertTrue(asbool('Y'))
        self.assertFalse(asbool('n'))
        self.assertFalse(asbool(False))
        self.assertTrue(asbool(True))

    def test_load_model(self):
        self.assertEqual(load_model('gpypi.utils:asbool'), asbool)
        self.assertEqual(load_model(asbool), asbool)

    def test_recursivley_find_file(self):
        file_ = recursivley_find_file(os.path.dirname(
            os.path.abspath(gpypi.__file__)), 'test_pypi.py')
        self.assertRegexpMatches(file_, '.+gpypi/tests/test_pypi.py$')
