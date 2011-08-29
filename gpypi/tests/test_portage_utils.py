#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
import shutil

from gpypi.portage_utils import *
from gpypi.tests import *
from gpypi.exc import *

import mocker


class TestPortageUtils(BaseTestCase):
    """Unittests for portage functions"""

    def setUp(self):
        self.overlay = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.overlay)
        self.mocker = mocker.Mocker()

    def test_get_all_overlays(self):
        """docstring for test_get_all_overlays"""
        #env = self.mocker.patch(ENV)
        #env['PORTDIR_OVERLAY']
        #self.mocker.result(self.overlay)
        #self.mocker.replay()
        d = PortageUtils.get_all_overlays()
        # TODO: mock overlays locations

    def test_installed_ver(self):
        """"""
        pass

    def test_is_valid_atom(self):
        """"""
        pass

    def test_ebuild_exists(self):
        """docstring for test_ebuild_exists"""
        self.assertTrue(PortageUtils.ebuild_exists('sys-devel/gcc'))
        self.assertFalse(PortageUtils.ebuild_exists('sys-devel/foobar'))

    def test_unpack_ebuild(self):
        """"""
        pass

    def test_find_s_dir(self):
        """"""
        pass

    def test_workdir(self):
        """docstring for test_workdir"""
        pass

    def test_portdir_overlay(self):
        """docstring for test_portdir_overlay"""
        pass

    def test_portage_tmpdir(self):
        """docstring for test_portage_tmpdir"""
        pass

    def test_get_portdir(self):
        """docstring for test_get_portdir"""
        pass

    def test_get_keyword(self):
        """docstring for test_get_keyword"""
        pass

    def test_make_ebuild_dir(self):
        """docstring for test_make_ebuild_dir"""
        ebuild_dir = PortageUtils.make_ebuild_dir('dev-python', 'foobar', self.overlay)
        self.assertTrue(os.path.exists(ebuild_dir))
        self.assertEqual(ebuild_dir.split('/')[-2:], ['dev-python', 'foobar'])

        with self.assertRaises(GPyPiCouldNotCreateEbuildPath):
            PortageUtils.make_ebuild_dir('dev-python', 'foobar', '/dev/null')
