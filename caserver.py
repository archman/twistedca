#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from twisted.internet import reactor

from util.cadata import caMeta, caMetaProxy
from cas.pv import PV
from cas.server import Server
from util.defs import *

def main():
    lmeta=caMeta(DBF.LONG)
    
    test=PV('test', value=['hello world'], meta=caMeta(DBF.STRING))
    test2=PV('test2', value=[42], meta=caMeta(DBF.LONG))
    test3=PV('test3', value=range(10), meta=caMetaProxy(test2.meta))

    p = Server(pvs=[test,test2,test3])
    
    reactor.run()
    
    p.close()

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    main()
