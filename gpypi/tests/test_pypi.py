#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests against live PyPi.
"""
import os
import unittest2

from yolk.pypi import CheeseShop

from gpypi.enamer import *
from gpypi.cli import *
from gpypi.tests import *

@unittest2.skipIf(not os.environ.get('TEST_LIVE_PYPI', None),
    "set TEST_LIVE_PYPI env variable to test against PyPi")
class TestPyPi(BaseTestCase):
    """"""
    def setUp(self):
        self.pypi = CheeseShop()
        self.all_packages = []
        for package in self.pypi.list_packages():
            (pn, vers) = self.pypi.query_versions_pypi(package)
            for version in vers:
                try:
                    url = self.pypi.get_download_urls(pn, version)[0]
                except IndexError:
                    pass
                    # TODO: log how many packages do not have URL
                else:
                    self.all_packages.append((pn, version))
                    # TODO: cache entries with cPickle

    #def test_get_vars_against_pypi(self):
        #for package_name, version in self.all_packages:
            #try:
                #d = Enamer.get_vars(url, pn, version)
            #except:
                #pass
            ## TODO: maybe assert some of dictionary stuff?
        #self.fail('Fail!')

    def test_get_vars_against_pypi(self):
        for package_name, version in self.all_packages:
            #try:
            main(['create', package_name, version])
            #except:
                #pass
            # TODO: maybe assert some of dictionary stuff?
        self.fail('Fail!')
