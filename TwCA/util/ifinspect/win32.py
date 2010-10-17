# -*- coding: utf-8 -*-

import sys, socket, logging, array
log=logging.getLogger('TwCA.util.ifinspect.win32')
from socket import inet_ntoa, inet_aton, htonl, htons

from ctypes import *

from TwCA.util.ifinspect import interface
from TwCA.util.udp import int2addr

__all__ = ['win32']

class sockaddr_in(Structure):
    _fields_ = [('family', c_uint16),
                ('port', c_uint16),
                ('addr', c_uint32),
                ('zero', c_uint8*16)] # see note

    def __str__(self):
        return 'f %u a %s p %u'% \
            (self.family, int2addr(self.addr), self.port)

# the sockaddr_gen union is 8 bytes longer then sockaddr_in
# however this definition is padded
assert sizeof(sockaddr_in)==24

class INTERFACE_INFO(Structure):
    _fields_=[('flags', c_ulong),
              ('addr', sockaddr_in),
              ('bcast', sockaddr_in),
              ('netmask', sockaddr_in),
             ]

    def __str__(self):
        return ('flags: %x\naddr: %s\n'
                'bcast: %s\nnetmask: %s\n')\
               %(self.flags, self.addr, self.bcast, self.netmask)

assert sizeof(INTERFACE_INFO)==76

def win32():
    infolist=(INTERFACE_INFO*10)()

    a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    SIO_GET_INTERFACE_LIST=0x4004747f

    IFF_UP=0x1
    IFF_BROADCAST=0x2
    IFF_LOOPBACK=0x4

    SOCKET = c_ulong
    DWORD = c_ulong
    LPVOID = c_void_p
    LPDWORD = POINTER(DWORD)
    
    NULL=c_void_p()

    assert sizeof(SOCKET) == sizeof(c_void_p), "winsock SOCKETs must be pointers"

    WSAIoctl = windll.ws2_32.WSAIoctl
    WSAIoctl.restype = c_int
    WSAIoctl.argtypes = [ SOCKET,
                          DWORD,  # control code
                          LPVOID, # input buffer
                          DWORD,  # input buffer length
                          LPVOID, # output buffer
                          DWORD,  # output buffer length
                          LPDWORD,# output buffer length used
                          LPVOID,
                          LPVOID,
                        ]

    filled=DWORD(0)

    x=WSAIoctl(a.fileno(), 
               SIO_GET_INTERFACE_LIST,
               NULL, 0,
               infolist, sizeof(infolist), byref(filled),
               NULL, NULL)

    if x!=0:
        raise RuntimeError('ioctl returned error %d'%x)

    N=filled.value/sizeof(INTERFACE_INFO)

    iflist=set()

    for n,intr in enumerate(infolist[:N]):
        for attr in ('addr','netmask','bcast'):
            sa=getattr(intr,attr)
            sa.addr=socket.htonl(sa.addr)
            sa.port=socket.htons(sa.port)

        if intr.addr.family != socket.AF_INET:
            log.debug('Ignoring non-IPv4 interface %d %d',
                       n,intr.addr.family)
            continue

        if not intr.flags&IFF_UP:
            continue

        i=interface()
        i.name='intr%u'%n
        i.addr=int2addr(intr.addr.addr)
        # not using i.netmask

        if intr.flags&IFF_BROADCAST:
            i.broadcast=int2addr(intr.bcast.addr)

        if intr.flags&IFF_LOOPBACK:
            i.loopback=True

        iflist.add(i)

    i=interface()
    i.name='lo'
    i.addr='127.0.0.1'
    i.localhost=True
    
    iflist.add(i)

    return iflist

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    print win32()
