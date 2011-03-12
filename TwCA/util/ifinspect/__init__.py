# -*- coding: utf-8 -*-

"""
Provides one function getifinfo which returns
a list with information on each of the system
network interfaces
"""

import sys, logging, socket
log=logging.getLogger('TwCA.util.ifinspect')

__all__=['getifinfo',  'interface']


class interface(object):
    """Holds information about a network interface.
    """
    #: Interface name string (eg 'eth0')
    name=None
    #: Type of socket to use with this interface.
    #: Currently always AF_INET, but this may change.
    family=socket.AF_INET
    #: Interface network address as a string.
    #: For IPv4 addresses this is a dotted quad like '10.0.100.4'.
    addr=None
    #: None unless the interface supports broadcasts, then the broadcast
    #: address as a string.
    broadcast=None
    #: Is this the loopback inteface?
    loopback=None

    def __str__(self):
        info={}
        info['lo']=' loopback' if self.loopback else ''
        info['bcast']='bcast %s'%self.broadcast if self.broadcast else ''
        info.update(self.__dict__)
        return 'IF: %(name)s%(lo)s IPv4 %(addr)s %(bcast)s'%info

    def __repr__(self):
        return str(self)

def default():
    i=interface()
    i.name='def'
    i.addr='' # any address
    i.broadcast='255.255.255.255'
    i.loopback=False
    return set([i])

global ifinfo
ifinfo=None

def getifinfo(rebuild=False):
    """Returns a :class:`set` of :class:`interface` objects
    based on information collected from the host system.
    """
    global ifinfo
    if ifinfo is None or rebuild:

        try:
            if sys.platform in ('win32'):
                from win32 import win32
                ifinfo=win32()
            else:
                from unix import unix
                ifinfo=unix()

        except Exception,e:
            log.error("network iface detection failed: "+str(e))
            ifinfo=default()

    return ifinfo

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    iflist=getifinfo()
    for intr in iflist:
        print intr
