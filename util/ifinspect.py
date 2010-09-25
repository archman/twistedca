# -*- coding: utf-8 -*-

"""
Provides one function getifinfo which returns
a list with information on each of the system
network interfaces
"""

import sys, socket, logging, ctypes
log=logging.getLogger('util.ifinspect')
from socket import inet_ntoa, inet_aton, htonl, htons
from fcntl import ioctl

__all__=['getifinfo']

class interface(object):
    name=None
    family=socket.AF_INET
    addr=None
    broadcast=None
    loopback=None

    def __str__(self):
        info={}
        info['lo']=' loopback' if self.loopback else ''
        info['bcast']='bcast %s'%self.broadcast if self.broadcast else ''
        info.update(self.__dict__)
        return 'IF: %(name)s%(lo)s IPv4 %(addr)s %(bcast)s'%info

def unix():
    
    SIOCGIFCONF   =0x8912
    SIOCGIFFLAGS  =0x8913
    SIOCGIFBRDADDR=0x8919

    # Select interface flags
    IFF_UP=0x1
    IFF_BROADCAST=0x2
    IFF_LOOPBACK=0x8
    
    class sockaddr(ctypes.Structure):
        _fields_ = [('family', ctypes.c_uint16),
                   ('data', ctypes.c_uint8*14)]

    class sockaddr_in(ctypes.Structure):
        _fields_ = [('family', ctypes.c_uint16),
                   ('port', ctypes.c_uint16),
                   ('addr', ctypes.c_uint32),
                   ('zero', ctypes.c_uint8*8)]

    assert ctypes.sizeof(sockaddr)==ctypes.sizeof(sockaddr_in)
    
    class ifmap(ctypes.Structure):
        _fields = [('start', ctypes.c_ulong),
                   ('end', ctypes.c_ulong),
                   ('addr', ctypes.c_ushort),
                   ('irq', ctypes.c_char),
                   ('dma', ctypes.c_char),
                   ('port', ctypes.c_char)]
    
    class ifreq_ifru(ctypes.Union):
        _fields_ = [('addr', sockaddr),
                    ('sval', ctypes.c_short),
                    ('ival', ctypes.c_int),
                    ('map', ifmap),
                    ('strval', ctypes.c_char*16)]
    
    class ifreq(ctypes.Structure):
        _anonymous_ = ("ifru",)
        _fields_ = [('name', ctypes.c_char*16),
                    ('ifru', ifreq_ifru)]

    class ifconf(ctypes.Structure):
        _fields_ = [("len", ctypes.c_int),
                    ("req", ctypes.POINTER(ifreq))]

    if ctypes.sizeof(ctypes.c_int)==4:
        # lengths found on 32-bit Linux x86
        assert ctypes.sizeof(ifreq_ifru)==16, 'expect 16 not %u'%ctypes.sizeof(ifreq_ifru)
        assert ctypes.sizeof(ifreq)==32
    

    ifarr=ifreq*100
    arr=ifarr()
    conf=ifconf(len=ctypes.sizeof(ifarr),
                req=arr)

    a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    ioctl(a.fileno(), SIOCGIFCONF, buffer(conf))

    iflist=set()

    for intr in arr:
        if len(intr.name)==0:
            break

        if intr.addr.family==socket.AF_INET:
            iface=interface()
            iface.name=intr.name

            # cast from sockaddr to sockaddr_in
            addr=ctypes.cast(ctypes.byref(intr.addr),
                             ctypes.POINTER(sockaddr_in))[0]
            # go from integer in host order to string
            ip=inet_ntoa(inet_aton(str(htonl(addr.addr))))
            iface.addr=ip
            
            x=ioctl(a.fileno(), SIOCGIFFLAGS, buffer(intr))
            intr=ifreq.from_buffer_copy(x)
            
            if not intr.sval&IFF_UP:
                # only include active interfaces
                log.debug('%s is down, skipping...',iface.name)
                continue

            iface.loopback=bool(intr.sval&IFF_LOOPBACK)

            if intr.sval&IFF_BROADCAST:
                x=ioctl(a.fileno(), SIOCGIFBRDADDR, buffer(intr))
                intr=ifreq.from_buffer_copy(x)
                addr=ctypes.cast(ctypes.byref(intr.addr),
                                ctypes.POINTER(sockaddr_in))[0]
                ip=inet_ntoa(inet_aton(str(htonl(addr.addr))))
                iface.broadcast=ip

            iflist.add(iface)
        else:
            log.debug('Ignoring non IPv4 interface %s',intr.name)

    return iflist

global ifinfo
ifinfo=None

def getifinfo(rebuild=True):
    global ifinfo
    if ifinfo is None or rebuild:

        if sys.platform != 'WIN32':
            ifinfo=unix()
        else:
            raise NotImplemented('Network interface introspection not implemented')

    return ifinfo

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    iflist=getifinfo()
    for intr in iflist:
        print intr
