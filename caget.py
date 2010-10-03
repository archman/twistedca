#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys


from twisted.internet import reactor
from twisted.internet.defer import DeferredList
from cac.clichannel import CAClientChannel
from cac.get import CAGet
from util.defs import DBR_STRING, DBR_INT, DBF_STRING

def main():

    def channelCB(chan, status):
        print chan

    def data(result):
        print 'Data Received',result
        return result

    def stop(x):
        reactor.stop()
        return x

    chan=CAClientChannel(sys.argv[1], channelCB)

    gets=[]

    gets.append(CAGet(chan, DBR_STRING, 1).data)
    gets.append(CAGet(chan, DBR_INT, 100, dbf=DBF_STRING).data)

    for d in gets:
        d.addCallback(data)

    done=DeferredList(gets)
    done.addBoth(stop)

    reactor.run()

    print chan

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)

    main()
