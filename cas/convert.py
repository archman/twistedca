# -*- coding: utf-8 -*-

from defs import *
from copy import copy

class ConversionNotDefined(Exception):
    pass

def _noop(val, **kwargs):
    return val

def _fail(val, **kwargs):
    raise ConversionNotDefined()

def intconv(val, **kwargs):
    return int(val)

def floatconv(val, **kwargs):
    return float(val)

def intprint(val, **kwargs):
    return '%d'%value

def floatprint(val, prec=None, **kwargs):
    if prec is None:
        return '%g'%val
    else:
        return ("%%.%dg"%prec)%val

def printEnum(val, strs=[], **kwargs):
    if val>=len(strs) or val<0:
        return ''
    return strs[val]

def chooseEnum(val, strs=[], **kwargs):
    for i,s in enumerate(strs):
        if s==val:
            return i
    raise ValueError('Value is not a choice')

_default={DBF_STRING:'',
          DBF_INT   :0,
          DBF_FLOAT :0.0,
          DBF_ENUM  :0, # needs access to enum list
          DBF_CHAR  :0, # convert to char array
          DBF_LONG  :0,
          DBF_DOUBLE:0.0,
         }

def setValue(_, force, **kwargs):
    return force

# Excludes (X,X) cases
# (X,Y):None for special case
_converter={(DBF_STRING,DBF_INT)   :intconv,
            (DBF_STRING,DBF_FLOAT) :floatconv,
            (DBF_STRING,DBF_ENUM)  :chooseEnum,
            (DBF_STRING,DBF_CHAR)  :None, # convert to char array
            (DBF_STRING,DBF_LONG)  :intconv,
            (DBF_STRING,DBF_DOUBLE):floatconv,
            (DBF_INT,DBF_STRING)   :intprint,
            (DBF_INT,DBF_FLOAT)    :floatconv,
            (DBF_INT,DBF_ENUM)     :_noop,
            (DBF_INT,DBF_CHAR)     :intprint,
            (DBF_INT,DBF_LONG)     :_noop,
            (DBF_INT,DBF_DOUBLE)   :floatconv,
            (DBF_FLOAT,DBF_STRING) :floatprint,
            (DBF_FLOAT,DBF_INT)    :intconv,
            (DBF_FLOAT,DBF_ENUM)   :_noop,
            (DBF_FLOAT,DBF_CHAR)   :intprint,
            (DBF_FLOAT,DBF_LONG)   :_noop,
            (DBF_FLOAT,DBF_DOUBLE) :floatconv,
            (DBF_ENUM,DBF_STRING)  :printEnum,
            (DBF_ENUM,DBF_INT)     :_noop,
            (DBF_ENUM,DBF_FLOAT)   :floatconv,
            (DBF_ENUM,DBF_CHAR)    :_noop, #BUG: return char array?
            (DBF_ENUM,DBF_LONG)    :_noop,
            (DBF_ENUM,DBF_DOUBLE)  :floatconv,
            (DBF_CHAR,DBF_STRING)  :None, # convert from char array,
            (DBF_CHAR,DBF_INT)     :intprint,
            (DBF_CHAR,DBF_FLOAT)   :floatconv,
            (DBF_CHAR,DBF_ENUM)    :_noop, #BUG: interpret as string?
            (DBF_CHAR,DBF_LONG)    :_noop,
            (DBF_CHAR,DBF_DOUBLE)  :floatconv,
            (DBF_LONG,DBF_STRING)  :intprint,
            (DBF_LONG,DBF_INT)     :_noop,
            (DBF_LONG,DBF_FLOAT)   :floatconv,
            (DBF_LONG,DBF_ENUM)    :_noop,
            (DBF_LONG,DBF_CHAR)    :intprint,
            (DBF_LONG,DBF_DOUBLE)  :floatconv,
            (DBF_DOUBLE,DBF_STRING):floatprint,
            (DBF_DOUBLE,DBF_INT  ) :intconv,
            (DBF_DOUBLE,DBF_FLOAT) :_noop,
            (DBF_DOUBLE,DBF_ENUM)  :floatconv,
            (DBF_DOUBLE,DBF_CHAR)  :intconv,
            (DBF_DOUBLE,DBF_LONG)  :intconv,
           }

def visitAllValues(val, conv, **kwargs):
    val.value = conv(val.value, **kwargs)
    for f in ['display', 'warning', 'alarm', 'control']:
        u, l = getattr(val,f)
        u, l = conv(u, **kwargs), conv(l, **kwargs)

def dbr_convert(val,dbf):
    """Return a partial copy of the the given caValue
    with converted to a different native field
    type.
    
    The returned structure should not be modified as this
    may cause modifications to the original value.
    """

    ret=copy(val) # shallow copy
    
    if val.dbf==dbf:
        return ret
    
    scls=dbf_field_class(val.dbf)
    dcls=dbf_field_class(dbf)
    
    conv=_converter[(val.dbf,dbf)]
    
    extra={}
    if conv is None:
        # special cases
        if (val.dbf,dbf)==(DBF_STRING,DBF_CHAR):
            # clear associated
            visitAllValues(ret, setValue, force=0)
            ret.value=val.value[0]
            
            
        elif (val.dbf,dbf)==(DBF_CHAR,DBF_STRING):
            ret.value=[val.value[:40]]

        ret.dbf=dbf
        return ret

    elif scls==DBF_C_REAL:
        extra['prec']=val.precision

    elif val.dbf==DBF_ENUM:
        extra['strs']=val.strs

    visitAllValues(ret, conv, **extra)

    ret.dbf=dbf
    return ret
