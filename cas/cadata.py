# -*- coding: utf-8 -*-
"""
:mod:`cadata` -- (de)serialization for CA data types
====================================================
"""

from array import array
from struct import Struct

from util.ca import padString
import defs

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
        assert not isinstance(inp, str)
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

_dbr_value={defs.DBF_STRING:dbr_string,
            defs.DBF_INT   :dbr_int,
            defs.DBF_SHORT :dbr_short,
            defs.DBF_FLOAT :dbr_float,
            defs.DBF_ENUM  :dbr_enum,
            defs.DBF_CHAR  :dbr_char,
            defs.DBF_LONG  :dbr_long,
            defs.DBF_DOUBLE:dbr_double
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

_dbr_sts={defs.DBF_CHAR:dbr_sts_char,
          defs.DBF_DOUBLE:dbr_sts_double
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
_dbr_time={defs.DBF_INT   :dbr_time_short,
           defs.DBF_SHORT :dbr_time_short,
           defs.DBF_ENUM  :dbr_time_short,
           defs.DBF_CHAR  :dbr_time_char,
           defs.DBF_DOUBLE:dbr_time_double
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
_dbr_gr_integer={defs.DBF_INT:dbr_gr_int,
                 defs.DBF_SHORT:dbr_gr_int,
                 defs.DBF_CHAR:dbr_gr_char,
                 defs.DBF_LONG:dbr_gr_long,
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
_dbr_gr_real={defs.DBF_FLOAT:dbr_gr_float,
              defs.DBF_DOUBLE:dbr_gr_double,
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
_dbr_ctrl_integer={defs.DBF_INT:dbr_ctrl_int,
                 defs.DBF_SHORT:dbr_ctrl_int,
                 defs.DBF_CHAR:dbr_ctrl_char,
                 defs.DBF_LONG:dbr_ctrl_long,
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
_dbr_ctrl_real={defs.DBF_FLOAT:dbr_ctrl_float,
              defs.DBF_DOUBLE:dbr_ctrl_double,
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


class caValue(object):
    def __init__(self, dbf_native):
        self.dbf=dbf_native
        self.value=[]
        self.units=''
        self.stamp=0.0
        for f in ['status','severity','precision']:
            setattr(self, f, 0)
        for p in ['display', 'warning', 'alarm', 'control']:
            setattr(self, f, (None,None))
        self.strs=[]

    def tostring(self, dbr, count):
        dbf, meta = defs.dbr_to_dbf(dbr)
        assert self.dbf==dbf, 'tostring() is serialization, not a value conversion'
        metadata=''
        if meta==defs.DBR_PLAIN:
            pass
        elif meta==defs.DBR_STS:
            metadata=dbr_sts(self.dbf).pack(self.status, self.severity)
            
        elif meta==defs.DBR_TIME:
            ns=int((self.stamp%1)*1e9)
            metadata=dbr_time(self.dbf).pack(self.status, self.severity,
                                    int(self.stamp), ns)

        else:
            raise RuntimeError('meta data format not supported')

        data=dbr_value(self.dbf).pack(self.value[:count])
        return (padString(metadata+data), len(self.value[:count]))

    def fromstring(self, raw, dbr, count):
        dbf, meta = defs.dbr_to_dbf(dbr)
        assert self.dbf==dbf, 'fromstring() is serialization, not a value conversion'
        if meta==defs.DBR_PLAIN:
            pass

        elif meta==defs.DBR_STS:
            conv=dbr_sts(self.dbf)
            self.status, self.severity = conv.unpack(raw)
            raw=raw[conv.size:]

        elif meta==defs.DBR_TIME:
            conv=dbr_sts(self.dbf)
            self.status, self.severity, sec, nsec = conv.unpack(raw)
            self.stamp=sec+float(nsec)*1e-9
            raw=raw[conv.size:]

        else:
            raise RuntimeError('meta data format not supported')

        self.value = dbr_value(dbf).unpack(raw)
