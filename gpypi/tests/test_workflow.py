#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
import logging
import shutil
import unittest2

from gpypi.workflow import *
from gpypi.config import *
from gpypi.tests import *


class TestWorkflow(BaseTestCase):
    """Unittests for utilities"""

    def setUp(self):
        self.options = ConfigManager(['setup_py', 'pypi', 'ini'], [])
        self.options.configs['pypi'] = {}
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        self.metadata_filename = os.path.join(self.d, 'metadata.xml')

        self.handler = ListHandler()
        logging.getLogger().addHandler(self.handler)

    def test_command_fail(self):
        """"""
        w = Workflow(self.options, self.d)

        self.assertFalse(w.command('cat wikiwakiwoo'))
        self.assertEqual(2, len(self.handler.error))

    def test_metadata_all(self):
        """"""
        self.options.configs['ini'] = {
            'metadata_herd': 'python',
            'metadata_maintainer_description': 'I,me',
            'metadata_maintainer_email': 'foo,bar',
            'metadata_maintainer_name': 'foo@bar.com,bar@foo.com',
        }
        m = Metadata(self.options, self.d)
        m()

        filename = os.path.join(self.d, 'metadata.xml')
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(1, len(self.handler.info))
        self.assertEqual(open(filename).read(),
"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE pkgmetadata SYSTEM "http://www.gentoo.org/dtd/metadata.dtd">
<pkgmetadata>
\t<herd>python</herd>
\t<maintainer>
\t\t<email>foo</email>
\t\t<name>foo@bar.com</name>
\t\t<description>I</description>
\t</maintainer>
\t<maintainer>
\t\t<email>bar</email>
\t\t<name>bar@foo.com</name>
\t\t<description>me</description>
\t</maintainer>
\t<longdescription></longdescription>
</pkgmetadata>
""")

    def test_metadata_skip(self):
        """"""
        self.options.configs['ini'] = {'metadata_disable': True}
        m = Metadata(self.options, self.d)
        m()

        filename = os.path.join(self.d, 'metadata.xml')
        self.assertFalse(os.path.exists(filename))
        self.assertEqual(1, len(self.handler.warning))

    def test_metadata_noherd(self):
        """"""
        m = Metadata(self.options, self.d)
        m()

        self.assertTrue('no-herd' in open(self.metadata_filename).read())

    def test_metadata_echangelog_user(self):
        """"""
        self.options.configs['ini'] = {
            'metadata_use_echangelog_user': True,
        }
        os.environ['ECHANGELOG_USER'] = 'foobar <foo@bar.com>'
        m = Metadata(self.options, self.d)
        m()

        filename = os.path.join(self.d, 'metadata.xml')
        self.assertTrue('foo@bar.com' in open(filename).read())
        self.assertTrue('foobar' in open(filename).read())

    def test_metadata_exists(self):
        """"""
        open(self.metadata_filename, 'w')
        m = Metadata(self.options, self.d)
        m()

        self.assertEqual("", open(self.metadata_filename).read())
        self.assertEqual(1, len(self.handler.warning))

    @unittest2.expectedFailure
    def test_manifest_generation(self):
        """"""
        category = os.path.join(self.d, 'dev-python')
        os.mkdir(category)

        shutil.copy(os.path.join(self.SETUP_SAMPLES_DIR, 'most_simple_setup.tmpl'),
            os.path.join(category, 'foobar-1.0.ebuild'))
        r = Repoman(self.options, category)
        r()

        self.assertTrue(os.path.exists(os.path.join(category, 'Manifest')))
        # TODO: set PORTDIR_OVERLAY somehow ...

    def test_echangelog_commit(self):
        """"""
        # TODO: kind of a lot of mocking ...
