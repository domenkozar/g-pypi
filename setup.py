#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

from setuptools import setup, find_packages
from distutils.command.install_data import install_data

from gpypi2.sdist_ebuild import sdist_ebuild

class post_install(install_data):
    def run(self):
        install_data.run(self)

        # register sdist_ebuild command
        sdist_ebuild.register()

version = '0.1'

setup(name='gpypi2',
    version=version,
    description="creates ebuilds for Gentoo Linux from Python Package Index",
    long_description="""More at http://docs.fubar.si/gpypi2/""",
    keywords='gentoo linux distribution ebuild package pypi',
    author='Domen Kozar',
    author_email='domen@dev.si',
    url='http://bitbucket.org/iElectric/g-pypi2/',
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    packages=find_packages(),
    cmdclass={"install_data": post_install},
    classifiers=[
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Software Distribution',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Operating System :: Unix',
        'Environment :: Console',
    ],
    install_requires=[
        'unittest2',
        'jinja2',
        'yolk',
        'pygments',
        'argparse',
        'jaxml>=3.02',
        'metagen', #metadata.xml
    ],
    tests_require=[
        'nose',
        'mocker',
        'mock',
        'ScriptTest',
    ],
    extras_require={
        'docs': ["Sphinx", "sphinxcontrib-googleanalytics"],
    },
    entry_points={
        'console_scripts': ['gpypi2 = gpypi2.cli:main']
    },
)
