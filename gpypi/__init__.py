#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pkg_resources
__version__ = pkg_resources.get_distribution('g-pypi').version.replace('dev', '')
