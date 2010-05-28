#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests against live PyPi.
"""
import os
import unittest2

from yolk.pypi import CheeseShop

from gpypi2.enamer import *
from gpypi2.tests import *

@unittest2.skipIf(not os.environ.get('TEST_LIVE_PYPI', None),
    "set TEST_LIVE_PYPI env variable to test against PyPi")
class TestPyPi(BaseTestCase):
    """"""

    def test_get_vars_against_pypi(self):
        self.pypi = CheeseShop()
        for package in self.pypi.list_packages():
            (pn, vers) = self.pypi.query_versions_pypi(package)
            for version in vers:
                try:
                    url = self.pypi.get_download_urls(pn, version)[0]
                except IndexError:
                    pass
                    # TODO: log how many packages do not have URL
                else:
                    try:
                        d = Enamer.get_vars(url, pn, version)
                    except:
                        pass
                    # TODO: maybe assert some of dictionary stuff?
        self.fail('Fail!')
