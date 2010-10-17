# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('util.twisted')

from zope.interface import implements

from twisted.internet.defer import Deferred, succeed
from twisted.internet.tcp import Connector
from twisted.internet.protocol import Protocol, DatagramProtocol

from idman import DeferredManager
from ca import CAmessage
from interfaces import IConnectNotify


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
    implements(IConnectNotify)

    # save protocol since it is cleared from the
    # transport before connectionLost() is called
    __protocol=None
    
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

    def connectionMade(self, protocol):
        """connecting -> connected
        """
        self.__protocol=protocol
        self.__D=DeferredManager()
        self.__C.callback(self.__protocol)
        # now C fired, D armed

    def connectionLost(self, res):
        """connected -> disconnected
        """
        self.__C=DeferredManager()
        self.__D, D = DeferredManager(), self.__D
        if self.__protocol is not None:
            # the None case only happens if there was
            # an exception during the connection setup
            D.callback(self.__protocol)
            self.__protocol=None
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
    debug=False
    
    def __init__(self, tst, program, halt=True):
        self.tst, self.program=tst, program
        self.halt=halt
        
        self._dispatch_table={}
        self.done=Deferred()
        self.halted=False
        
        self.dest=None

        self._dispatch_default=self.expect

    def expect(self, pkt, x, y=None):
        self.tst.failIfEqual(len(self.program), 0,
                        'Received data after end of program')
        cmd, epkt = self.program.pop(0)
        self.tst.assertEqual(cmd, 'recv')
        
        self.tst.assertEqual(pkt.cmd,  epkt.cmd)
        self.tst.assertEqual(pkt.size, epkt.size)
        self.tst.assertEqual(pkt.dtype,epkt.dtype)
        self.tst.assertEqual(pkt.count,epkt.count)
        self.tst.assertEqual(pkt.p1,   epkt.p1)
        self.tst.assertEqual(pkt.p2,   epkt.p2)
        self.tst.assertEqual(pkt.body ,epkt.body)
        
        if self.debug:
            print 'Rx',pkt
        
        self.send()

    def send(self):
        
        while len(self.program)>0 and self.program[0][0]=='send':
            cmd, epkt = self.program.pop(0)

            if self.dest is None:
                self.transport.write(epkt.pack())
            else:
                self.transport.write(epkt.pack(), self.dest)

            if self.debug:
                print 'Tx', epkt

        if len(self.program)==0:
            if self.halt:
                self.transport.loseConnection()
                if self.debug:
                    print 'Halt'

            if self.debug:
                print 'Done'

            if not self.halted:
                self.done.callback(self)
                self.halted=True

class CAExpectProtocol(CAProtocol,CAExpectMixen):

    def connectionMade(self):
        self.send()


class CAExpectDatagramProtocol(CADatagramProtocol,CAExpectMixen):

    def startProtocol(self):
        self.send()
