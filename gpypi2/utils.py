#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""

import os
import sys
import types
import logging

from portage.output import EOutput

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
    reload(module) # Might be out of date during tests
    del sys.path[0]
    return module


class PortageStreamHandler(logging.StreamHandler):
    """StreamHandler that does not add additional newline"""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            fs = "%s" # removed trailing newline
            if not hasattr(types, "UnicodeType"): #if no unicode support...
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
        # TODO: nocolors

        class LoggingOutput(EOutput):
            """"""
            self.output = None
            def _write(self, file, msg):
                self.output = msg

        l = LoggingOutput()
        if record.levelno == logging.WARN:
            l.ewarn(output)
        elif record.levelno == logging.INFO:
            l.einfo(output)
        elif record.levelno == logging.ERROR:
            l.eerror(output)

        return l.output or output
