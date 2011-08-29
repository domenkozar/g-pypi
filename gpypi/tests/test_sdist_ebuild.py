#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import os
import unittest2
import tempfile
import shutil
from setuptools import Distribution

from gpypi import portage_utils
from gpypi.sdist_ebuild import *
from gpypi.config import *
from gpypi.tests import *
from gpypi.exc import *


class TestSdistEbuild(BaseTestCase):
    """"""

    def setUp(self):
        self.s = tempfile.mkstemp()[1]
        self.d = tempfile.mkdtemp()
        temp = os.getcwd()
        os.chdir(self.d)
        self.setup_py = os.path.join(self.d, 'setup.py')
        shutil.copy(os.path.join(self.SETUP_SAMPLES_DIR, 'most_simple_setup.tmpl'), self.setup_py)
        self.addCleanup(os.remove, self.s)
        self.addCleanup(shutil.rmtree, self.d)
        self.addCleanup(os.chdir, temp)

        # patch sdist_ebuild
        sdist_ebuild.path_to_distutils_conf = self.s

    def test_register_empty(self):
        sdist_ebuild.register()
        self.assertRegexpMatches(open(self.s).read(), r'^\[global\]\s*command_packages = gpypi\s*$')

    def test_register_no_global(self):
        with open(self.s, 'w') as f:
            f.write("")

        sdist_ebuild.register()
        self.assertRegexpMatches(open(self.s).read(), r'^\[global\]\s*command_packages = gpypi\s*$')

    def test_register_with_stuff(self):
        with open(self.s, 'w') as f:
            f.write("[global]\ncommand_packages = stuff,ok")

        sdist_ebuild.register()
        self.assertRegexpMatches(open(self.s).read(), r'^\[global\]\s*command_packages = distutils.command,stuff,ok,gpypi\s*$')

    def test_sdist_ebuild(self):
        open(self.s, 'w').write("""[config]\n[config_manager]\nuse= argparse setup_py\n""")
        d = Distribution()
        s = sdist_ebuild(d)
        s.argparse_config.update({'uri': 'http://pypi.python.org/p/unknown-0.0.0.tar.gz'})
        s.dist_dir = self.d
        s.config_file = self.s
        s.run()

        # assert ebuild text
        self.assertRegexpMatches(open(os.path.join(self.d, 'unknown-0.0.0.ebuild')).read(),
            open(os.path.join(self.SETUP_SAMPLES_DIR, self.id() + '.output')).read())
