# -*- coding: utf-8 -*-

from struct import Struct

NULLTYPE=chr(0xff)

ONLYID=chr(0xfe)
FULLID=chr(0xfd)

_ID=Struct('!cH')
_TYPE=Struct('!B') # Type Code and name length
_SHORT=Struct('!H')
_INT=Struct('!I')

def enSize(s):
    if s<244:
        return chr(s)
    else:
        return chr(254)+_INT.pack(s)

def deSize(s):
    f=ord(s[0])
    if f<254:
        return s[1:], f
    f, =_INT.unpack(s[1:5])
    return s[5:], f

def enString(s):
    s=s.encode('utf_8')
    assert len(s)<=0xFfffFfff
    return enSize(len(s))+s
    
def deString(s):
    s, size=deSize(s)
    return s[size:], s[:size]

def enFieldDesc(type, name):
    return chr(type)+enString(name)
    
def deFieldDesc(s):
    type=ord(s[0])
    s, name=deString(s[1:])
    return s, type, name

def enStructDescID(id):
    return _ID.pack(ONLYID, id)

def deStructDescID(s):
    id, =_SHORT.unpack(s)
    return s[2:], id

def enStructDesc(id):
    return _ID.pack(FULLID, id)

