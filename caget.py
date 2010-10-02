#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys


from twisted.internet import reactor
from cac.clichannel import CAClientChannel

def channelCB(chan, status):
    if status:
        print 'connected',chan
    else:
        print 'lost',chan

def main():
    chan=CAClientChannel(sys.argv[1], channelCB)

    reactor.run()

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)

    main()
