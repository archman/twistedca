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
Config.empty=Config(next=None)
Config.default=Config(next=Config.empty)

def _build_defaultconfig():
    c={'sport':0,
       'cport':0,
       'addrs':[], # client address list
       'autoaddrs':False,
       'nameservs':[],
       'srvaddrs':[], 'srvignoreaddrs':[], 'srvautoaddrs':False,
       'beaconaddrs':[], 'beaconautoaddrs':False,
      }
    Config.empty._props=c # empty config for unit tests
    
    Config.default=Config(Config.empty)

    Config.default.sport=SERVER_PORT
    Config.default.cport=CLIENT_PORT
    Config.default.addrs=[('127.0.0.1',SERVER_PORT)]
    Config.default.autoaddrs=True
    #Config.default.nameservs=[]
    Config.default.srvautoaddrs=True
    Config.default.beaconaddrs=['127.0.0.1']
    Config.default.beaconautoaddrs=True

_build_defaultconfig()
