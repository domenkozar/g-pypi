#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""

import os
import sys
import types
import logging

from portage.output import EOutput
from pkg_resources import EntryPoint


def load_model(dotted_name):
    """Load module with dotted name syntax

    Example::

        >>> load_model('gpypi.utils:import_path') # doctest: +ELLIPSIS
        <function import_path at 0x...>

    """
    if isinstance(dotted_name, basestring):
        return EntryPoint.parse('x=%s' % dotted_name).load(False)
    else:
        # Assume it's already loaded.
        return dotted_name


def import_path(fullpath):
    """Import a file with full path specification. Allows one to
    import from anywhere, something __import__ does not do.

    :param fullpath: Path to a Python file to import
    :type string:
    :rtype: Python module

    """
    # http://zephyrfalcon.org/weblog/arch_d7_2002_08_31.html
    path, filename = os.path.split(fullpath)
    filename, ext = os.path.splitext(filename)
    sys.path.insert(0, path)
    module = __import__(filename)
    reload(module)  # Might be out of date during tests
    del sys.path[0]
    return module


def asbool(obj):
    """Do everything to consider ``obj`` as  boolean.

    Example::

        >>> asbool('y')
        True

    :raises: :exc:`ValueError` -- If object could not be booleanized.

    """
    if isinstance(obj, (str, unicode)):
        obj = obj.strip().lower()
        if obj in ['true', 'yes', 'on', 'y', 't', '1']:
            return True
        elif obj in ['false', 'no', 'off', 'n', 'f', '0']:
            return False
        else:
            raise ValueError("String is not true/false: %r" % obj)
    return bool(obj)


class PortageStreamHandler(logging.StreamHandler):
    """StreamHandler that does not add additional newline"""

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            fs = "%s"  # removed trailing newline
            if not hasattr(types, "UnicodeType"):  # if no unicode support...
                stream.write(fs % msg)
            else:
                try:
                    if (isinstance(msg, unicode) and
                        getattr(stream, 'encoding', None)):
                        fs = fs.decode(stream.encoding)
                        try:
                            stream.write(fs % msg)
                        except UnicodeEncodeError:
                            stream.write((fs % msg).encode(stream.encoding))
                    else:
                        stream.write(fs % msg)
                except UnicodeError:
                    stream.write(fs % msg.encode("UTF-8"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class PortageFormatter(logging.Formatter):
    """Logging formatter that uses :class:`portage.output.EOutput`
    to format messages like portage output.
    """

    def format(self, record):
        """format according to logging level"""
        output = logging.Formatter(self._fmt, self.datefmt).format(record)

        class LoggingOutput(EOutput):
            """"""
            output = None

            def _write(self, file, msg):
                self.output = msg

        l = LoggingOutput()
        if record.levelno == logging.WARN:
            l.ewarn(output)
        elif record.levelno == logging.INFO:
            l.einfo(output)
        elif record.levelno == logging.ERROR:
            l.eerror(output)
        else:
            output = output + '\n'

        return l.output or output


def recursivley_find_file(path, filename, in_text=None):
    """Find filename in specified path recursively"""
    for root, dirs, files in os.walk(path):
        if filename in files:
            file_ = os.path.join(root, filename)
            if not in_text:
                return file_
            elif in_text in open(file_).read():
                return file_
