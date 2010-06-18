#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exceptions module
=============================
"""


class GPyPiException(Exception):
    """Core exception class, all exception inherit from this class."""

class GPyPiInvalidAtom(GPyPiException):
    """Raised when determining Portage Atom did not succeed."""

class GPyPiNoSetupFile(GPyPiException):
    """Raised if no setup.py was found."""

class GPyPiNoDistribution(GPyPiException):
    """Raised if unpacked directory could not be found."""

class GPyPiCouldNotUnpackEbuild(GPyPiException):
    """Raised if unpacking failed."""
