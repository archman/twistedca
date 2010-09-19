#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from twisted.internet import reactor

from cas.pv import PV
from cas.server import Server
from cas.defs import DBF_STRING, DBF_LONG

def main():
    
    test=PV('test', dbf=DBF_STRING, value=['hello world'])
    test2=PV('test2', dbf=DBF_LONG, value=[42])
    test3=PV('test3', dbf=DBF_LONG, value=range(10), maxcount=None)
    
    p = Server(pvs=[test,test2,test3])
    
    reactor.run()

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    main()
