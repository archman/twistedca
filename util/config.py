# -*- coding: utf-8 -*-

from defs import CLIENT_PORT, SERVER_PORT

__all__=['Config']

class Config(object):
    _props={"this value not used":None}
    _next=None

    def __init__(self, next=None):
        self._next=next if next else self.default
        self._props={} # create a per instance dictionary

    def set(self, **kwargs):
        self._props.update(kwargs)
        return self

    def __getattr__(self, name):
        a=self._props.get(name)
        if a is None and self._next is not None:
            a=getattr(self._next, name)
        return a

# The default configuration
Config.default=Config(next=None)

def _build_defaultconfig():
    c={'sport':SERVER_PORT,
       'cport':CLIENT_PORT,
       'addrs':[('127.0.0.1',SERVER_PORT)],
       'autoaddrs':False
      }
    
    Config.default._props=c

_build_defaultconfig()
