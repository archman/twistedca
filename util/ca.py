# -*- coding: utf-8 -*-

from struct import Struct

__all__ = ['CAmessage', 'packSearchBody']

header = Struct('!HHHHII')
header_extend = Struct ('!II')

searchbody=Struct('!Hxxxxxx')

packSearchBody=searchbody.pack

def padString(inp):
    if len(inp)==0:
        return '\0'*8
    elif inp[-1:]=='\0':
        inp=inp+'\0'
    p=len(inp)%8
    if p!=0:
        inp=inp+'\0'*(8-p)
    return inp

def packCAerror(cid, sts, msg, pkt):
    body=pkt.pack()+padString(msg)
    err=CAmessage(cmd=11, size=len(body),
                  p1=cid, p2=sts, body=body)
    return err

class CAmessage(object):

    def __init__(self, body='', **kwargs):
        parts = ['cmd','size','dtype','count','p1','p2']
        self.body=body
        for arg, val in kwargs.iteritems():
            if arg not in parts:
                raise AttributeError('Invalid keyword '+arg)
            setattr(self,arg,val)
        for p in parts:
            if hasattr(self,p) or p is 'body':
                continue
            setattr(self,p,0)

    @classmethod
    def unpack(cls, msg):
        m = cls()
        msg = m.unpack_into(msg)
        return (m, msg)

    def unpack_into(self, msg):
        self.cmd, self.size, \
        self.dtype, self.count, \
        self.p1, self.p2 = header.unpack(msg[:16])
        
        if self.size==0xffff and self.count==0:
            self.size, self.count = \
                header_extend.unpack(msg[16:24])
            self.body=msg[24:(24+self.size)]
            return msg[(24+self.size):]
        else:
            self.body=msg[16:(16+self.size)]
            return msg[(16+self.size):]

    def pack(self):
        return header.pack(self.cmd, self.size, \
        self.dtype, self.count, \
        self.p1, self.p2) + self.body

    def __repr__(self):
        return 'Type: %(cmd)d %(size)d %(dtype)x %(count)d %(p1)x %(p2)x "%(body)s"'%\
            self.__dict__
