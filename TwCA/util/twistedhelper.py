# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('util.twisted')

from twisted.internet.defer import Deferred, succeed
from twisted.internet.tcp import Connector
from twisted.internet.protocol import Protocol, DatagramProtocol

from TwCA.util.idman import DeferredManager
from TwCA.util.ca import CAmessage

class DeferredConnector(Connector):
    """Provides Deferred s for connection life cycle
    
    Provides a three state machine.
    
        /------------->---------------\
    connected <- connecting <-> disconnected -> shutdown
    
    The shutdown state is signalled when the connected Deferred()
    is called with None.  The disconnected Deferred() will always
    have been called before.
    
    When in the shutdown state both Deferred()s have been called.
    
    Initial (disconnect): D fired, C ready
    connect         : fire D, arm C    [implicit]
    connectionMade  : arm  D, fire C
    connectionFailed: fire D, fire C (None)
    connectionLost  : fire D, arm C
    """
    
    def __init__(self, *args, **kws):
        Connector.__init__(self, *args, **kws)
        
        self.__C=DeferredManager()
        self.__D=DeferredManager()
        self.__D.callback(None)

    @property
    def whenCon(self):
        return self.__C.get()

    @property
    def whenDis(self):
        return self.__D.get()

    def connectionFailed(self, res):
        """connecting -> disconnected
        """
        self.__C, C = DeferredManager(), self.__C
        C.callback(None)
        # now C armed, D fired

        Connector.connectionFailed(self, res)

    def connectionMade(self):
        """connecting -> connected
        """
        # save protocol since it is cleared from the
        # transport before connectionLost() is called
        self.__protocol=self.transport.protocol
        self.__D=DeferredManager()
        self.__C.callback(self.__protocol)
        # now C fired, D armed

    def connectionLost(self, res):
        """connected -> disconnected
        """
        self.__C=DeferredManager()
        self.__D, D = DeferredManager(), self.__D
        D.callback(self.__protocol)
        del self.__protocol
        # now C armed, D fired

        Connector.connectionLost(self, res)

class CAProtocol(Protocol):

    def _unknown_action(self, pkt, _):
        log.warning('Unknown TCP packet %d',pkt.cmd)

    def dataReceived(self, msg):

        msg=self.__in_buffer+msg

        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
            
            hdl = self._dispatch_table.get(pkt.cmd, self._dispatch_default)
        
            hdl(pkt, self)

        self.__in_buffer=msg # save remaining

    _dispatch_table=None
    _dispatch_default=_unknown_action
    __in_buffer=''

class CADatagramProtocol(DatagramProtocol):

    def _unknown_action(self, pkt, _):
        log.warning('Unknown UDP packet %d',pkt.cmd)

    def datagramReceived(self, msg, peer):
        
        while msg is not None and len(msg)>=16:

            pkt, msg = CAmessage.unpack(msg)

            hdl = self._dispatch_table.get(pkt.cmd, self._dispatch_default)

            hdl(pkt, self, peer)

        if len(msg)>0:
            log.warning('dropping incomplete message %s',repr(msg))

    _dispatch_table=None
    _dispatch_default=_unknown_action

class CAExpectMixen(object):
    noisy=False
    
    def __init__(self, tst, program, halt=True):
        self.tst, self.program=tst, program
        self.halt=halt
        
        self._dispatch_table={}
        
        self.dest=None

        self._dispatch_default=self.expect

    def expect(self, pkt, x, y=None):
        cmd, epkt = self.program.pop(0)
        self.tst.assertEqual(cmd, 'recv')
        
        self.tst.assertEqual(pkt.cmd,  epkt.cmd)
        self.tst.assertEqual(pkt.size, epkt.size)
        self.tst.assertEqual(pkt.dtype,epkt.dtype)
        self.tst.assertEqual(pkt.count,epkt.count)
        self.tst.assertEqual(pkt.p1,   epkt.p1)
        self.tst.assertEqual(pkt.p2,   epkt.p2)
        self.tst.assertEqual(pkt.body ,epkt.body)
        
        self.send()

    def send(self):
        
        while len(self.program)>0 and self.program[0][0]=='send':
            cmd, epkt = self.program.pop(0)

            if self.dest is None:
                self.transport.write(epkt.pack())
            else:
                self.transport.write(epkt.pack(), self.dest)

        if len(self.program)==0 and self.halt:
            self.transport.loseConnection()

class CAExpectProtocol(CAProtocol,CAExpectMixen):

    def connectionMade(self):
        self.send()


class CAExpectDatagramProtocol(CADatagramProtocol,CAExpectMixen):

    def startProtocol(self):
        self.send()
