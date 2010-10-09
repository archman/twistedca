# -*- coding: utf-8 -*-

from struct import Struct
from twisted.internet.udp import Port

__all__=['SharedUDP','int2addr','addr2int']

class SharedUDP(Port):
    """A UDP socket which can share
    a port with other similarly configured
    sockets.  Broadcasts to this port will
    be copied to all sockets.
    However, unicast traffic will only be
    delivered to one.
    """
    
    def createInternetSocket(self):
        import socket
        sock=Port.createInternetSocket(self)
        opt=socket.SO_REUSEADDR
        if hasattr(socket, 'SO_REUSEPORT'):
            opt=socket.SO_REUSEPORT
        sock.setsockopt(socket.SOL_SOCKET, opt, 1)
        sock.setsockopt(socket.SOL_SOCKET,
                        socket.SO_BROADCAST, 1)
        return sock


_IP=Struct('!I')

def int2addr(num):
    """
    Convert a 32-bit integer in MSB order to a IP string
    """
    from socket import inet_ntoa
    return inet_ntoa(_IP.pack(num))

def addr2int(addr):
    """Convert a IP string to an integer in MSB order
    """
    from socket import inet_aton
    return _IP.unpack(inet_aton(addr))[0]

