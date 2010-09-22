# -*- coding: utf-8 -*-
"""
:mod:`cadata` -- (de)serialization for CA data types
====================================================
"""

from array import array
from struct import Struct

from util.ca import padString
from defs import *
from convert import dbr_convert

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
        assert not isinstance(inp, str), 'Must be an array of strings'
        ret=''
        for s in inp:
            ret=ret+padString(s)
        return ret

    def unpack(self, bstr):
        #TODO: how is an array of strings actually stored?
        return [bstr.rstrip('\0')]
        #ret=[]
        #for i in range(len(bstr)/40):
            #ret.append( bstr[i*40:(i+1)*40].rstrip('\0') )
        #return ret

# value
dbr_string=caString()
dbr_int=ValueArray('h')
dbr_short=dbr_int
dbr_float=ValueArray('f')
dbr_enum=dbr_int
dbr_char=ValueArray('B')
dbr_long=ValueArray('i')
dbr_double=ValueArray('d')

_dbr_value={DBF_STRING:dbr_string,
            DBF_INT   :dbr_int,
            DBF_SHORT :dbr_short,
            DBF_FLOAT :dbr_float,
            DBF_ENUM  :dbr_enum,
            DBF_CHAR  :dbr_char,
            DBF_LONG  :dbr_long,
            DBF_DOUBLE:dbr_double
           }
def dbr_value(type):
    """Fetch the (un)packer for the given field type.
    
    The converter pack/unpack functions take one argument
    which is an list, array, or string.
    :param type: a DBF type
    :rtype: In instance of :class:`Struct` or :class:`ValueArray`
    """
    return _dbr_value[type]

# status, severity
dbr_sts_default=Struct('!hh')
dbr_sts_char=Struct('!hhx')
dbr_sts_double=Struct('!hhxxxx')

_dbr_sts={DBF_CHAR:dbr_sts_char,
          DBF_DOUBLE:dbr_sts_double
         }
def dbr_sts(type):
    """Fetch the status meta-data (un)packer for the given field type.
    
    The converter pack/unpack functions take two arguments
    which are integers (status, and severity).
    :param type: a DBF type
    :rtype: In instance of :class:`Struct`
    """
    return _dbr_sts.get(type, dbr_sts_default)

# status, severity, ts_sec, ts_nsec, value
dbr_time_default=Struct('!hhII')
dbr_time_short=Struct('!hhIIxx')
dbr_time_char=Struct('!hhIIxxx')
dbr_time_double=Struct('!hhIIxxxx')
_dbr_time={DBF_INT   :dbr_time_short,
           DBF_SHORT :dbr_time_short,
           DBF_ENUM  :dbr_time_short,
           DBF_CHAR  :dbr_time_char,
           DBF_DOUBLE:dbr_time_double
           }
def dbr_time(type):
    """Fetch the time meta-data (un)packer for the given field type.
    
    The converter pack/unpack functions take four arguments
    which are integers (status, severity, seconds, and nanoseconds).
    :param type: a DBF type
    :rtype: In instance of :class:`Struct`
    """
    return _dbr_time.get(type, dbr_time_default)

# status, severity, units, dU, dL, aU, wU, wL, aL
dbr_gr_int=Struct('!hh8shhhhhh')
dbr_gr_char=Struct('!hh8sccccccx')
dbr_gr_long=Struct('!hh8siiiiii')
_dbr_gr_integer={DBF_INT:dbr_gr_int,
                 DBF_SHORT:dbr_gr_int,
                 DBF_CHAR:dbr_gr_char,
                 DBF_LONG:dbr_gr_long,
                }
def dbr_gr_integer(type):
    """Fetch the GR meta-data (un)packer for the given integer field type.
    
    The converter pack/unpack functions take nine arguments:
    status, severity, units (a string), display high, display low,
    alarm high, warning high, warning low, alarm low.
    :param type: a DBF type
    :rtype: In instance of :class:`Struct`
    """
    return _dbr_gr_integer[type]

# status, severity, precision, units, dU, dL, aU, wU, wL, aL
dbr_gr_float=Struct('!hhhxx8sffffff')
dbr_gr_double=Struct('!hhhxx8sdddddd')
_dbr_gr_real={DBF_FLOAT:dbr_gr_float,
              DBF_DOUBLE:dbr_gr_double,
             }
def dbr_gr_real(type):
    """Fetch the GR meta-data (un)packer for the given real field type.
    
    The converter pack/unpack functions take ten arguments:
    status, severity, precision, units (a string), display high, display low,
    alarm high, warning high, warning low, alarm low.
    :param type: a DBF type
    :rtype: In instance of :class:`Struct`
    """
    return _dbr_gr_real[type]

# status, severity, #strings, 26x enum strings, value
dbr_gr_enum=Struct('!hhh' + '16c'*26 + 'H')

# status, severity, units, dU, dL, aU, wU, wL, aL, cU, cL
dbr_ctrl_int=Struct('!hh8shhhhhhhh')
dbr_ctrl_char=Struct('!hh8sccccccccx')
dbr_ctrl_long=Struct('!hh8siiiiiiii')
_dbr_ctrl_integer={DBF_INT:dbr_ctrl_int,
                 DBF_SHORT:dbr_ctrl_int,
                 DBF_CHAR:dbr_ctrl_char,
                 DBF_LONG:dbr_ctrl_long,
                }
def dbr_ctrl_integer(type):
    """Fetch the ctrl meta-data (un)packer for the given integer field type.
    
    The converter pack/unpack functions take eleven arguments:
    status, severity, units (a string), display high, display low,
    alarm high, warning high, warning low, alarm low, control high,
    and control low.
    :param type: a DBF type
    :rtype: In instance of :class:`Struct`
    """
    return _dbr_gr_integer[type]

# status, severity, precision, units, dU, dL, aU, wU, wL, aL, cU, cL
dbr_ctrl_float=Struct('!hhhxx8sffffffff')
dbr_ctrl_double=Struct('!hhhxx8sdddddddd')
_dbr_ctrl_real={DBF_FLOAT:dbr_ctrl_float,
              DBF_DOUBLE:dbr_ctrl_double,
             }
def dbr_ctrl_real(type):
    """Fetch the ctrl meta-data (un)packer for the given real field type.
    
    The converter pack/unpack functions take twelve arguments:
    status, severity, precision, units (a string), display high, display low,
    alarm high, warning high, warning low, alarm low, control high,
    and control low.
    :param type: a DBF type
    :rtype: In instance of :class:`Struct`
    """
    return _dbr_gr_real[type]

dbr_ctrl_enum=dbr_gr_enum

# Special

# status, severity, ackt, acks, value
dbr_stsack_string=Struct('!HHHH40s')

_default={DBF_STRING:'',
          DBF_INT   :0,
          DBF_FLOAT :0.0,
          DBF_ENUM  :0,
          DBF_CHAR  :0,
          DBF_LONG  :0,
          DBF_DOUBLE:0.0,
         }

def dbf_default(dbf):
    return _default[dbf]

_limits={DBF_STRING:(None,None),
          DBF_INT   :((-2**16)-1,2**16),
          DBF_FLOAT :(-1e38,1e38),
          DBF_ENUM  :((-2**16)-1,2**16),
          DBF_CHAR  :((-2**8)-1,2**8),
          DBF_LONG  :((-2**31)-1,2**31),
          DBF_DOUBLE:(-1e308,1e308),
         }

def dbf_default_limits(dbf):
    return _limits[dbf]


class caMeta(object):
    def __init__(self, dbf):
        self.dbf=dbf
        self.units=''
        self.stamp=0.0
        for f in ['status','severity','precision']:
            setattr(self, f, 0)
        l=dbf_default_limits(dbf)
        for p in ['display', 'warning', 'alarm', 'control']:
            setattr(self, p, l)
        self.strs=[]

    def __str__(self):
        return ('Meta %(dbf)d %(status)d %(severity)s '+ \
                '%(stamp)f %(units)s %(precision)d '+ \
                '%(display)s %(warning)s %(alarm)s %(control)s') \
                % self.__dict__


def tostring(value, meta, dbr, count):
    dbf, metacls = dbr_to_dbf(dbr)

    value, meta = dbr_convert(dbf, value, meta)

    metadata=''
    if metacls==DBR_PLAIN:
        pass
    elif metacls==DBR_STS:
        metadata=dbr_sts(meta.dbf).pack(meta.status, meta.severity)
        
    elif metacls==DBR_TIME:
        ns=int((meta.stamp%1)*1e9)
        metadata=dbr_time(meta.dbf).pack(meta.status, meta.severity,
                                int(meta.stamp), ns)

    else:
        raise RuntimeError('meta data format not supported')

    data=dbr_value(meta.dbf).pack(value[:count])
    return (padString(metadata+data), len(value[:count]))

def fromstring(raw, meta, dbr, count):
    dbf, metacls = dbr_to_dbf(dbr)
    rmeta=caMeta(dbf)

    if metacls==DBR_PLAIN:
        pass

    elif metacls==DBR_STS:
        conv=dbr_sts(dbf)
        rmeta.status, rmeta.severity = conv.unpack(raw[:conv.size])
        raw=raw[conv.size:]

    elif metacls==DBR_TIME:
        conv=dbr_sts(dbf)
        rmeta.status, rmeta.severity, sec, nsec = conv.unpack(raw[:conv.size])
        rmeta.stamp=sec+float(nsec)*1e-9
        raw=raw[conv.size:]

    else:
        raise RuntimeError('meta data format not supported')

    value = dbr_value(dbf).unpack(raw)
    print value
    value, rmeta = dbr_convert(dbf, value, rmeta)

    return (value, rmeta)
