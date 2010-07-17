#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import unittest2


class BaseTestCase(unittest2.TestCase):
    """Common unittesting utility helpers"""


class ListHandler(logging.Handler):
    """Mocking handler that stores logging messages in the class itself"""


    def __init__(self, *a, **kw):
        self.debug = []
        self.warning = []
        self.info = []
        self.error = []
        logging.Handler.__init__(self, *a, **kw)

    def emit(self, record):
        getattr(self, record.levelname.lower()).append(record.getMessage())

    def reset(self):
        for attr in dir(self):
            if isinstance(getattr(self, attr), list):
                setattr(self, attr, [])
