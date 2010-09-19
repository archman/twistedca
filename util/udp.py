# -*- coding: utf-8 -*-

from twisted.internet.udp import Port

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
