# -*- coding: utf-8 -*-

import sys, socket, logging, ctypes, array
log=logging.getLogger('TwCA.util.ifinspect.unix')
from socket import inet_ntoa, inet_aton, htonl, htons
from fcntl import ioctl

from TwCA.util.ifinspect import interface
from TwCA.util.udp import int2addr

__all__ = ['unix']

if sys.version_info < (2, 6, 0):
    def str2struct(string, cstruct):
        """Cast a python string containing a byte
        array into a C structure
        """
        from ctypes import sizeof, pointer, POINTER, memmove

        assert not hasattr(cstruct, 'contents'), "must _not_ be a POINTER type"
        # copy to a writable buffer first
        a=array.array('c')
        a.fromstring(string)

        # find address
        base, l = a.buffer_info()
        assert l==sizeof(cstruct), 'string size must match struct size'

        # cast buffer pointer to struct pointer
        b=ctypes.cast(base, POINTER(cstruct))

        # make a copy
        c=cstruct()
        memmove(pointer(c), b, sizeof(c))

        return c
else:
    def str2struct(string,cstruct):
        return cstruct.from_buffer_copy(buffer(string))

def unix():
    """Query interfaces
    """
    
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
            ip=int2addr(socket.htonl(addr.addr))
            iface.addr=ip
            
            x=ioctl(a.fileno(), SIOCGIFFLAGS, buffer(intr))

            intrflags=str2struct(x,ifreq)
            assert intrflags.name==intr.name

            flags=intrflags.sval
            
            if not flags&IFF_UP:
                # only include active interfaces
                log.debug('%s is down, skipping...',iface.name)
                continue

            iface.loopback=bool(flags&IFF_LOOPBACK)

            if flags&IFF_BROADCAST:
                x=ioctl(a.fileno(), SIOCGIFBRDADDR, buffer(intr))
                #intr=ifreq.from_buffer_copy(x)
                intr=str2struct(x,ifreq)
                addr=ctypes.cast(ctypes.byref(intr.addr),
                                ctypes.POINTER(sockaddr_in))[0]
                ip=int2addr(htonl(addr.addr))
                iface.broadcast=ip

            iflist.add(iface)
        else:
            log.debug('Ignoring non IPv4 interface %s',intr.name)

    return iflist
