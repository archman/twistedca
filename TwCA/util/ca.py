# -*- coding: utf-8 -*-

from struct import Struct
from cadata import padString, dbr_data_size

__all__ = ['CAmessage', 'packSearchBody']

header = Struct('!HHHHII')
header_extend = Struct ('!II')

searchbody=Struct('!Hxxxxxx')

monitormask=Struct('!xxxxxxxxxxxxHxx')

packSearchBody=searchbody.pack

def packCAerror(cid, sts, msg, pkt):
    body=pkt.pack()+padString(msg)
    err=CAmessage(cmd=11, size=len(body),
                  p1=cid, p2=sts, body=body)
    return err

class CAmessage(object):

    def __init__(self, cmd=0, size=0, dtype=0, count=0,
                       p1=0, p2=0, body=''):
        self.cmd, self.size, self.dtype = cmd, size, dtype
        self.count, self.p1, self.p2 = count, p1, p2
        self.body=body

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
