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
    if hasattr(val, '__len__'):
        return map(lambda v:int(v), val)
    else:
        return int(val)

def floatconv(val, **kwargs):
    if hasattr(val, '__len__'):
        return map(lambda v:float(v), val)
    else:
        return float(val)
        
def intprint(val, **kwargs):
    # use normal list printing and strip off the brackets
    return [str(val)[1:-1]]

def floatprint(val, prec=None, **kwargs):
    if prec is None:
        spec='%g'
    else:
        spec="%%.%dg"%prec

    def _helper(a,b):
        if len(a)>0:
            a=a+', '
        return spec%val

    if not hasattr(val, '__len__'):
        val=[val]

    return [reduce(_helper, val, '')]

def printEnum(val, strs=[], **kwargs):
    if val>=len(strs) or val<0:
        return ''
    return strs[val]

def chooseEnum(val, strs=[], **kwargs):
    for i,s in enumerate(strs):
        if s==val:
            return i
    raise ValueError('Value is not a choice')

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
    for f in ['display', 'warning', 'alarm', 'control']:
        u, l = getattr(val,f)
        u, l = conv(u, **kwargs), conv(l, **kwargs)

def dbr_convert(dbf, val, meta):
    """Return a partial copy of the the given caValue
    with converted to a different native field
    type.
    
    The returned structure should not be modified as this
    may cause modifications to the original value.
    
    @returns: (val, meta)
    """

    rmeta=copy(meta) # shallow copy
    
    if meta.dbf==dbf:
        return (copy(val), rmeta)
    
    conv=_converter[(meta.dbf,dbf)]
    print (meta.dbf,dbf),conv

    if conv is None:
        # special cases
        if (meta.dbf,dbf)==(DBF_STRING,DBF_CHAR):
            # clear associated

            visitAllValues(rmeta, lambda _: 0)
            ret=reduce(str.__add__,val,'')
            
            
        elif (meta.dbf,dbf)==(DBF_CHAR,DBF_STRING):
            visitAllValues(rmeta, lambda _: None)
            ret=[val[i:(i+40)] for i in range(0,len(val),40)]

        rmeta.dbf=dbf
        return (copy(ret), rmeta)

    visitAllValues(rmeta, conv,
                   prec=meta.precision,
                   strs=meta.strs)
    ret=conv(val, prec=meta.precision,
             strs=meta.strs)

    rmeta.dbf=dbf
    return (copy(ret), rmeta)
