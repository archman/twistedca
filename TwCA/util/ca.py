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

# thrown when an incomplete packet is encountered
class CAIncomplete(Exception):
    pass

class CAmessage(object):

    def __init__(self, cmd=0, size=0, dtype=0, count=0,
                       p1=0, p2=0, body=buffer('')):
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
        self.p1, self.p2 = header.unpack(buffer(msg,0,16))

        if self.size==0xffff and self.count==0:
            if len(msg)<24:
                raise CAIncomplete()
            self.size, self.count = \
                header_extend.unpack(buffer(msg,16,8))
            self.body=buffer(msg,24,self.size)
            rem=buffer(msg,24+self.size)
        else:
            self.body=buffer(msg,16,self.size)
            rem=buffer(msg,16+self.size)

        if len(self.body)<self.size:
            raise CAIncomplete()

        return rem

    def pack(self):
        return header.pack(self.cmd, self.size, \
        self.dtype, self.count, \
        self.p1, self.p2) + str(self.body)

    def check(self):
        exp=dbr_data_size(self.dtype, self.count)
        if exp!=len(self.body):
            raise RuntimeError('Packet with inconsistent header')

    def __eq__(self, O):
        for a in ['cmd','size','dtype','count','p1','p2']:
            if getattr(self, a) != getattr(O, a):
                return False
        return True

    def __ne__(self, O):
        return not (self==O)

    def __repr__(self):
        return 'Type: %(cmd)d %(size)d %(dtype)x %(count)d %(p1)x %(p2)x "%(body)s"'%\
            self.__dict__
