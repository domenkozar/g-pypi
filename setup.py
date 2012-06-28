#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from distutils.command.install_data import install_data


class post_install(install_data):
    def run(self):
        install_data.run(self)

        # register sdist_ebuild command
        from gpypi.sdist_ebuild import sdist_ebuild
        sdist_ebuild.register()


setup(name='g-pypi',
    version='0.3',
    description="Manages ebuilds for Gentoo Linux using information from Python Package Index",
    long_description="""More at http://g-pypi.readthedocs.org/en/latest/""",
    keywords='gentoo linux distribution ebuild package pypi',
    author='Domen Kozar',
    author_email='domen@dev.si',
    url='https://github.com/iElectric/g-pypi',
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
        'metagen',  # metadata.xml
        'sphinxcontrib-googleanalytics',
        # also needs to install gentoolkit and gentoolkit-dev
    ],
    tests_require=[
        'nose',
        'mocker',
        'mock',
        'ScriptTest',
    ],
    entry_points={
        'console_scripts': ['gpypi = gpypi.cli:main']
    },
)
