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

    def data(data, pv, dbf):
        value,meta=data
        print pv,dbf,value
        return data

    def stop(x):
        reactor.stop()
        return x

    gets=[]

    for pv in sys.argv[1:]:
        chan=CAClientChannel(pv, channelCB)

        for dbr, count, dbf in [(DBR_STRING, 1  , None),
                                (DBR_INT   , None, DBF_STRING),
                                (DBR_INT   , None, None),
                                (DBR_INT   , None, DBF_DOUBLE),
                                (DBF_DOUBLE   , None, DBR_INT),
                                (DBF_DOUBLE   , None, None),
                               ]:
            gets.append(CAGet(chan, dbr, count, dbf).data)

            gets[-1].addCallback(data, pv, dbr)

    done=DeferredList(gets)
    done.addBoth(stop)

    reactor.run()

    print chan

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)

    main()
