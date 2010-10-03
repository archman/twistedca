#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys


from twisted.internet import reactor
from twisted.internet.defer import DeferredList
from cac.clichannel import CAClientChannel
from cac.get import CAGet
from util.defs import *

def main():

    def channelCB(chan, status):
        print chan

    def data(result):
        print 'Data Received',result
        return result

    def stop(x):
        reactor.stop()
        return x

    gets=[]

    for pv in sys.argv[1:]:
        chan=CAClientChannel(pv, channelCB)

        for dbr, count, dbf in [(DBR_STRING, 1  , None),
                                (DBR_INT   , 100, DBF_STRING),
                                (DBR_INT   , 100, None),
                                (DBR_INT   , 100, DBF_DOUBLE),
                                (DBF_DOUBLE   , 100, DBR_INT),
                                (DBF_DOUBLE   , 100, None),
                               ]:
            gets.append(CAGet(chan, dbr, count, dbf).data)

    for d in gets:
        d.addCallback(data)

    done=DeferredList(gets)
    done.addBoth(stop)

    reactor.run()

    print chan

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)

    main()
