#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncore
#from util.timer import Queue, Timer
import cas.endpoint as endpoint

def main():
    
    p = endpoint.UDPpeer(('localhost',5064))
    
    asyncore.loop()

if __name__=='__main__':
    main()
