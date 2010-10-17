# -*- coding: utf-8 -*-

import logging

__version__ = 'pre1'

if not hasattr(logging, 'NullHandler'):
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

__h=NullHandler()
logging.getLogger("TwCA").addHandler(__h)
