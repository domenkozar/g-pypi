#!/usr/bin/python
"""
This file is here to be copied to portage root
and used for distribution in for easier unittesting
"""

from setuptools import setup

version='0.1'

setup(name="portage",
    license="GPL-2",
    version=version,
    description="",
    long_description="",
    maintainer="",
    author="",
    author_email="",
    url="",
    keywords="",
    classifiers=[],
    packages=['portage', '_emerge'],
    package_dir={'':'pym'},
    include_package_data = True,
)
