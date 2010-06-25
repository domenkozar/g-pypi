#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from gpypi2.utils import *
from gpypi2.tests import *
from gpypi2.tests import test_ebuild

import mocker


class TestUtils(BaseTestCase):
    """Unittests for utilities"""
    HERE = os.path.dirname(os.path.abspath(__file__))

    def test_import_path(self):
        module = import_path(os.path.join(self.HERE, 'test_ebuild.py'))
        self.assertTrue(module.TestEbuild)
