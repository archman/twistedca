# -*- coding: utf-8 -*-

import asyncore, socket

class UDPdispatcher(asyncore.dispatcher):
    """Since the default dispatcher does not provide
    wrappers for the UDP socket ops
    """
    def __init__(self, *args, **kwargs):
        asyncore.dispatcher.__init__(self, *args, **kwargs)

    def sendto(self, data, peer):
        try:
            return self.socket.sendto(data, 0, peer)
        except socket.error, why:
            if why.args[0] == EWOULDBLOCK:
                return 0
            elif why.args[0] in (ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED):
                self.handle_close()
                return 0
            else:
                raise

    def recvfrom(self, buffer_size):
            try:
                data, peer = self.socket.recvfrom(buffer_size)
                if not data:
                    # a closed connection is indicated by signaling
                    # a read condition, and having recv() return 0.
                    self.handle_close()
                    return ('', None)
                else:
                    return (data, peer)
            except socket.error, why:
                # winsock sometimes throws ENOTCONN
                if why.args[0] in [ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED]:
                    self.handle_close()
                    return ('', None)
                else:
                    raise
