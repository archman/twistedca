# -*- coding: utf-8 -*-
"""
:mod:`cadata` -- (de)serialization for CA data types
====================================================
"""

from array import array
from struct import Struct
from time import time

from util.ca import padString
from defs import *
from convert import dbr_convert_value, dbr_convert_meta_value
from copy import copy

__all__ = ['caMeta', 'caMetaProxy', 'tostring','fromstring']

ETEST=array('H',[0x1234])
BIGENDIAN=ETEST.tostring()[0]=='\x12'

class ValueArray(object):
    """Something compatible :class:`Struct` which deals with
    array values
    """
    
    def __init__(self, prim):
        self.prim=prim

    def pack(self, values):
        data=array(self.prim, values)
        if not BIGENDIAN:
            data.byteswap()
        return data.tostring()

    def unpack(self, bstr):
        data=array(self.prim)
        data.fromstring(bstr)
        if not BIGENDIAN:
            data.byteswap()
        return data

class caString(object):

    def pack(self,inp):
        """In a string array each entry but the last is padded to 40 bytes.
        The last is padded to the dword (8 byte) boundary
        """
        assert not isinstance(inp, str), 'Must be an array of strings'
        ret=''
        for i,s in enumerate(inp):
            if i==len(inp)-1:
                ret+=s
            else:
                ret+=s+(40-len(s))*'\0'
        return padString(ret)

    def unpack(self, bstr):
        if len(bstr)==0 or bstr[0]=='\0':
            return []
        ret=[]
        N=(len(bstr)/40)+1
        for i in range(N):
            S= bstr[i*40:(i+1)*40].rstrip('\0')
            if len(S)==0:
                continue
            ret.append( S )
        return ret

# value
dbr_string=caString()
dbr_int=ValueArray('h')
dbr_short=dbr_int
dbr_float=ValueArray('f')
dbr_enum=dbr_int
dbr_char=ValueArray('B')
dbr_long=ValueArray('i')
dbr_double=ValueArray('d')

_dbr_value={DBF.STRING:dbr_string,
            DBF.INT   :dbr_int,
            DBF.SHORT :dbr_short,
            DBF.FLOAT :dbr_float,
            DBF.ENUM  :dbr_enum,
            DBF.CHAR  :dbr_char,
            DBF.LONG  :dbr_long,
            DBF.DOUBLE:dbr_double
           }
def dbr_value(type):
    """Fetch the (un)packer for the given field type.
    
    The converter pack/unpack functions take one argument
    which is an list, array, or string.
    :param type: a DBF type
    :rtype: In instance of :class:`Struct` or :class:`ValueArray`
    """
    return _dbr_value[type]

_dbf_element_size={DBF.STRING:40,
                   DBF.INT   :2,
                   DBF.SHORT :2,
                   DBF.FLOAT :4,
                   DBF.ENUM  :2,
                   DBF.CHAR  :1,
                   DBF.LONG  :4,
                   DBF.DOUBLE:8
                  }
def dbf_element_size(dbf):
    return _dbf_element_size[dbf]

_dbr_meta={
    # no meta
    DBR.STRING     :(Struct(''), META.PLAIN),
    DBR.INT        :(Struct(''), META.PLAIN),
    DBR.SHORT      :(Struct(''), META.PLAIN),
    DBR.FLOAT      :(Struct(''), META.PLAIN),
    DBR.ENUM       :(Struct(''), META.PLAIN),
    DBR.CHAR       :(Struct(''), META.PLAIN),
    DBR.LONG       :(Struct(''), META.PLAIN),
    DBR.DOUBLE     :(Struct(''),    META.PLAIN),
    # status, severity
    DBR.STS_STRING :(Struct('!hh'), META.STS),
    DBR.STS_SHORT  :(Struct('!hh'), META.STS),
    DBR.STS_FLOAT  :(Struct('!hh'), META.STS),
    DBR.STS_ENUM   :(Struct('!hh'), META.STS),
    DBR.STS_CHAR   :(Struct('!hhx'), META.STS),
    DBR.STS_LONG   :(Struct('!hh'),  META.STS),
    DBR.STS_DOUBLE :(Struct('!hhxxxx'), META.STS),
    # status, severity, ts_sec, ts_nsec
    DBR.TIME_STRING:(Struct('!hhII'),   META.TIME),
    DBR.TIME_INT   :(Struct('!hhIIxx'), META.TIME),
    DBR.TIME_FLOAT :(Struct('!hhII'),   META.TIME),
    DBR.TIME_ENUM  :(Struct('!hhII'),   META.TIME),
    DBR.TIME_CHAR  :(Struct('!hhIIxxx'),META.TIME),
    DBR.TIME_LONG  :(Struct('!hhII'),   META.TIME),
    DBR.TIME_DOUBLE:(Struct('!hhIIxxxx'),META.TIME),
    # status, severity, units, dU, dL, aU, wU, wL, aL
    DBR.GR_SHORT   :(Struct('!hh8shhhhhh'), META.GR),
    DBR.GR_CHAR    :(Struct('!hh8sccccccx'), META.GR),
    DBR.GR_LONG    :(Struct('!hh8siiiiii'), META.GR),
    # status, severity, precision, units, dU, dL, aU, wU, wL, aL
    DBR.GR_FLOAT   :(Struct('!hhhxx8sffffff'), META.GR|METAPARTS.REAL),
    DBR.GR_DOUBLE  :(Struct('!hhhxx8sdddddd'), META.GR|METAPARTS.REAL),
    # status, severity, #strings, 26x enum strings
    DBR.GR_ENUM    :(Struct('!hhh' + '26s'*16), META.STS|METAPARTS.ENUM),
    # status, severity, units, dU, dL, aU, wU, wL, aL, cU, cL
    DBR.CTRL_SHORT :(Struct('!hh8shhhhhhhh'), META.CTRL),
    DBR.CTRL_CHAR  :(Struct('!hh8sccccccccx'), META.CTRL),
    DBR.CTRL_LONG  :(Struct('!hh8siiiiiiii'), META.CTRL),
    DBR.CTRL_FLOAT :(Struct('!hhhxx8sffffffff'), META.CTRL|METAPARTS.REAL),
    DBR.CTRL_DOUBLE:(Struct('!hhhxx8sdddddddd'), META.CTRL|METAPARTS.REAL),
    DBR.STSACK_STRING:(Struct('!HHHH40s'), METAPARTS.SPEC),
   }
# duplicates
for dup, src in [(DBR.STS_INT,     DBR.STS_SHORT),
                 (DBR.TIME_INT,    DBR.TIME_SHORT),
                 (DBR.GR_INT,      DBR.GR_SHORT),
                 (DBR.CTRL_INT,    DBR.CTRL_SHORT),
                 (DBR.GR_STRING,   DBR.STS_STRING),
                 (DBR.CTRL_STRING, DBR.STS_STRING),
                 (DBR.CTRL_ENUM,   DBR.GR_ENUM),
                 (DBR.PUT_ACKT,    DBR.SHORT),
                 (DBR.PUT_ACKS,    DBR.SHORT),
                 (DBR.CLASS_NAME,  DBR.STRING),
                ]:
    _dbr_meta[dup]=_dbr_meta[src]
def dbr_meta(dbr):
    """
    Return the meta-data converter for the given dbr type
    
    Returns: (converter obj, meta-parts bitmask)
    """
    return _dbr_meta[dbr]

_default={DBF.STRING:'',
          DBF.INT   :0,
          DBF.FLOAT :0.0,
          DBF.ENUM  :0,
          DBF.CHAR  :0,
          DBF.LONG  :0,
          DBF.DOUBLE:0.0,
         }

def dbf_default(dbf):
    return _default[dbf]

_limits={DBF.STRING:(None,None),
          DBF.INT   :((-2**16)-1,2**16),
          DBF.FLOAT :(-1e38,1e38),
          DBF.ENUM  :((-2**16)-1,2**16),
          DBF.CHAR  :((-2**8)-1,2**8),
          DBF.LONG  :((-2**31)-1,2**31),
          DBF.DOUBLE:(-1e308,1e308),
         }

def dbf_default_limits(dbf):
    return _limits[dbf]

class caMetaProxy(object):
    """Allow a view of another meta-data object
    with partial copy-on-write behavior
    """
    def __init__(self, meta, ro=False):
        object.__setattr__(self, '_meta', meta)
        object.__setattr__(self, '_ro', ro)

    @property
    def ro(self):
        return self._ro

    @property
    def meta(self):
        return self._meta

    def __getattr__(self, name):
        return getattr(self._meta, name)

    def __setattr__(self, name, val):
        if self._ro:
            raise TypeError('caMetaProxy in read-only mode')
        object.__setattr__(self, name, val)

class caMeta(object):
    def __init__(self, dbf, units='', stamp=0.0,
                       status=0, severity=0, precision=0,
                       **kwargs):
        self.dbf, self.units, self.stamp=dbf, units, stamp
        self.status, self.severity = status, severity
        self.precision=precision
        l=dbf_default_limits(dbf)
        for p in ['display', 'warning', 'alarm', 'control']:
            setattr(self, p, kwargs.pop(p,l))
        self.strs=kwargs.pop('strs',[])
        if len(kwargs)>0:
            raise TypeError('Unexpected keyword arguments %s',str(kwargs.keys()))

    @property
    def ro(self):
        return False

    @property
    def meta(self):
        return self

    def __str__(self):
        return ('Meta dbf:%(dbf)d sts:%(status)d sev:%(severity)s '+ \
                'ts:%(stamp)f egu:%(units)s prec:%(precision)d '+ \
                'disp:%(display)s W:%(warning)s E:%(alarm)s C:%(control)s') \
                % self.__dict__

    def __eq__(self, o):
        for a in ['dbf', 'units', 'stamp', 'status','severity','precision', \
                  'display', 'warning', 'alarm', 'control']:
            if getattr(self,a)!=getattr(o,a):
                return False
        return True

def printMeta(meta, cls):
    dbr=dbf_to_dbr(meta.dbf, cls)

    # Use the meta de/encoder mask
    _, mmask=dbr_meta(dbr)

    if mmask==0:
        return '\n'
    m=''
    
    if mmask&METAPARTS.STS:
        m='\nSev: %s Sts: %s'%(meta.severity, meta.status)

    if mmask&METAPARTS.TIME:
        from time import ctime
        try:
            ts=ctime(meta.stamp)
        except ValueError:
            ts='Invalid(%.2f)'%meta.stamp
        m+='\nTime: %s\n'%ts
        return m

    if mmask&METAPARTS.REAL:
        m+='\nPrecision: %s'%meta.precision

    if mmask&METAPARTS.ENUM:
        m+='\nStrings: '+str(meta.strs)


    if mmask&METAPARTS.GR:
        m+='\nUnits: '+meta.units
        m+="\nDisplay: %s\nWarning: %s\nError: %s"% \
            (meta.display, meta.warning, meta.alarm)

    if mmask&METAPARTS.CTRL:
        m+="\nControl: %s"%(meta.control,)

    return m+'\n'


def tostring(value, meta, dbr, count):
    dbf, metacls = dbr_to_dbf(dbr)

    # value converters
    vconv = dbr_convert_value(meta.dbf, dbf)
    mconv = dbr_convert_meta_value(meta.dbf, dbf)

    # meta encoder
    mencode, mmask=dbr_meta(dbr)

    value = vconv(value, prec=meta.precision,
                         strs=meta.strs)

    mlist=[]

    if mmask&METAPARTS.STS:
        mlist=[meta.status, meta.severity]

    if mmask&METAPARTS.TIME:
        s=int(meta.stamp)-POSIX_TIME_AT_EPICS_EPOCH
        ns=int((meta.stamp%1)*1e9)
        mlist+=[s,ns]
    
    if mmask&METAPARTS.REAL:
        mlist.append(meta.precision)

    if mmask&METAPARTS.ENUM:
        N=len(meta.strs[:16])
        mlist.append(N)
        mlist+=meta.strs[:16]
        if N:
            mlist+=['']*(16-N)

    if mmask&METAPARTS.GR:
        mlist.append(meta.units)
        # dU, dL, aU, wU, wL, aL
        mlist+=[meta.display[1], meta.display[0],
                meta.alarm[1],   meta.warning[1],
                meta.warning[0], meta.alarm[0],
               ]
        
    if mmask&METAPARTS.CTRL:
        # cU, cL
        mlist+=[meta.control[1], meta.control[0]]

    metadata=mencode.pack(*mlist)

    data=dbr_value(dbf).pack(value[:count])

    return (padString(metadata+data), len(value[:count]))

def fromstring(raw, dbr, count, meta):
    dbf, metacls = dbr_to_dbf(dbr)
    rmeta=copy(meta)

    # value converters
    vconv = dbr_convert_value(dbf, meta.dbf)
    mconv = dbr_convert_meta_value(dbf, meta.dbf)

    # meta decoder
    mdecode, mmask=dbr_meta(dbr)

    rawmeta=list(mdecode.unpack(raw[:mdecode.size]))
    raw=raw[mdecode.size:]

    if mmask&METAPARTS.STS:
        rmeta.status=STATUS.fromInt(rawmeta.pop(0))
        rmeta.severity=SEVERITY.fromInt(rawmeta.pop(0))

    if mmask&METAPARTS.TIME:
        sec=rawmeta.pop(0)
        nsec=rawmeta.pop(0)
        rmeta.stamp=sec+POSIX_TIME_AT_EPICS_EPOCH+float(nsec)*1e-9

    if mmask&METAPARTS.REAL:
        rmeta.precision=rawmeta.pop(0)

    if mmask&METAPARTS.ENUM:
        nstrs=min(16, rawmeta.pop(0))
        assert len(rawmeta)==16
        rmeta.strs=[s.rstrip('\0') for s in rawmeta[:nstrs]]
            
        rawmeta=[]

    if mmask&METAPARTS.GR:
        rmeta.units=rawmeta.pop(0)
        vals=map(lambda x:mconv(x, prec=rmeta.precision),rawmeta[:6])
        rawmeta=rawmeta[6:]
        dU, dL, aU, wU, wL, aL = vals
        
        rmeta.display=(dL,dU)
        rmeta.warning=(wL,wU)
        rmeta.alarm  =(aL,aU)

    if mmask&METAPARTS.CTRL:
        vals=map(lambda x:mconv(x, prec=rmeta.precision),rawmeta[:2])
        rawmeta=rawmeta[:2]
        cU, cL = vals

        rmeta.control=(cL,cU)

    if dbf!=DBF.STRING:
        # remove zero padding from value
        dlen=dbf_element_size(dbf)*count
        raw=raw[:dlen]

    value = dbr_value(dbf).unpack(raw)

    value = vconv(value, prec=rmeta.precision,
                         strs=rmeta.strs)

    return (value, rmeta)
