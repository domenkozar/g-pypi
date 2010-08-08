#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

from setuptools import setup, find_packages


version = '0.1'

setup(name='g-pypi2',
    version=version,
    description="creates ebuilds for Gentoo Linux from Python Package Index",
    long_description="""""", # TODO: provide long description from docs index.rst
    keywords='gentoo linux distribution ebuild package pypi',
    author='Domen Kozar',
    author_email='domen@dev.si',
    url='http://bitbucket.org/iElectric/g-pypi2/',
 #   license='BSD',
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    packages=find_packages(),
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
