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
    return [str(list(val))[1:-1]]

def floatprint(val, prec=None, **kwargs):
    if prec is None:
        spec='%g'
    else:
        spec="%%.%dg"%prec

    def _helper(a,b):
        if len(a)>0:
            a=a+', '
        return a+spec%b

    if not hasattr(val, '__len__'):
        val=[val]

    return [reduce(_helper, val, '')]

def printEnum(val, strs=[], **kwargs):
    if val>=len(strs) or val<0:
        return ''
    return strs[val]

def chooseEnum(val, strs=[], **kwargs):
    assert len(strs)>0, 'enum needs strings'

    def chooseOne(v):
        for i,s in enumerate(strs):
            if s==v:
                return i
        raise ValueError('Value is not a choice')
    return map(chooseOne, val)

def str_as_carray(val, **kwargs):
    def stringify(v):
        v=v[:40]
        #v+=(40-len(v))*'\0'
        return v

    return reduce(str.__add__, map(stringify, val) ,'')

def carray_as_str(val, **kwargs):
    import array
    if isinstance(val, array.array):
        return [val.tostring().rstrip('\0')]
    return [reduce(str.__add__,map(chr,val),'')]

# Excludes (X,X) cases
# (X,Y):None when no conversion is needed
_converter_value={
            (DBF.STRING,DBF.INT)   :intconv,
            (DBF.STRING,DBF.FLOAT) :floatconv,
            (DBF.STRING,DBF.ENUM)  :chooseEnum,
            (DBF.STRING,DBF.CHAR)  :str_as_carray,
            (DBF.STRING,DBF.LONG)  :intconv,
            (DBF.STRING,DBF.DOUBLE):floatconv,
            (DBF.INT,DBF.STRING)   :intprint,
            (DBF.INT,DBF.FLOAT)    :floatconv,
            #(DBF.INT,DBF.ENUM)     :_noop,
            #(DBF.INT,DBF.CHAR)     :_noop,
            #(DBF.INT,DBF.LONG)     :_noop,
            (DBF.INT,DBF.DOUBLE)   :floatconv,
            (DBF.FLOAT,DBF.STRING) :floatprint,
            (DBF.FLOAT,DBF.INT)    :intconv,
            (DBF.FLOAT,DBF.ENUM)   :intconv,
            (DBF.FLOAT,DBF.CHAR)   :intprint,
            (DBF.FLOAT,DBF.LONG)   :intconv,
            #(DBF.FLOAT,DBF.DOUBLE) :_noop,
            (DBF.ENUM,DBF.STRING)  :printEnum,
            #(DBF.ENUM,DBF.INT)     :_noop,
            (DBF.ENUM,DBF.FLOAT)   :floatconv,
            #(DBF.ENUM,DBF.CHAR)    :_noop, #BUG: return char array?
            #(DBF.ENUM,DBF.LONG)    :_noop,
            (DBF.ENUM,DBF.DOUBLE)  :floatconv,
            (DBF.CHAR,DBF.STRING)  :carray_as_str,
            #(DBF.CHAR,DBF.INT)     :_noop,
            (DBF.CHAR,DBF.FLOAT)   :floatconv,
            #(DBF.CHAR,DBF.ENUM)    :_noop, #BUG: interpret as string?
            #(DBF.CHAR,DBF.LONG)    :_noop,
            (DBF.CHAR,DBF.DOUBLE)  :floatconv,
            (DBF.LONG,DBF.STRING)  :intprint,
            #(DBF.LONG,DBF.INT)     :_noop,
            (DBF.LONG,DBF.FLOAT)   :floatconv,
            #(DBF.LONG,DBF.ENUM)    :_noop,
            #(DBF.LONG,DBF.CHAR)    :_noop,
            (DBF.LONG,DBF.DOUBLE)  :floatconv,
            (DBF.DOUBLE,DBF.STRING):floatprint,
            (DBF.DOUBLE,DBF.INT  ) :intconv,
            #(DBF.DOUBLE,DBF.FLOAT) :_noop,
            (DBF.DOUBLE,DBF.ENUM)  :floatconv,
            (DBF.DOUBLE,DBF.CHAR)  :intconv,
            (DBF.DOUBLE,DBF.LONG)  :intconv,
           }
def dbr_convert_value(from_dbf, to_dbf):
    return _converter_value.get((from_dbf, to_dbf), _noop)

def store_zero(val, **kwargs):
    return 0

def store_none(val, **kwargs):
    return None

_converter_meta={
            (DBF.STRING,DBF.INT)   :store_zero,
            (DBF.STRING,DBF.FLOAT) :store_zero,
            (DBF.STRING,DBF.ENUM)  :store_zero,
            (DBF.STRING,DBF.CHAR)  :store_zero,
            (DBF.STRING,DBF.LONG)  :store_zero,
            (DBF.STRING,DBF.DOUBLE):store_zero,
            (DBF.INT,DBF.STRING)   :store_none,
            (DBF.INT,DBF.FLOAT)    :floatconv,
            (DBF.INT,DBF.CHAR)     :intprint,
            (DBF.INT,DBF.DOUBLE)   :floatconv,
            (DBF.FLOAT,DBF.STRING) :store_none,
            (DBF.FLOAT,DBF.INT)    :intconv,
            (DBF.FLOAT,DBF.ENUM)   :intconv,
            (DBF.FLOAT,DBF.CHAR)   :intprint,
            (DBF.FLOAT,DBF.LONG)   :intconv,
            (DBF.ENUM,DBF.STRING)  :store_none,
            (DBF.ENUM,DBF.FLOAT)   :floatconv,
            (DBF.ENUM,DBF.DOUBLE)  :floatconv,
            (DBF.CHAR,DBF.STRING)  :store_none,
            (DBF.CHAR,DBF.FLOAT)   :floatconv,
            (DBF.CHAR,DBF.DOUBLE)  :floatconv,
            (DBF.LONG,DBF.STRING)  :store_none,
            (DBF.LONG,DBF.FLOAT)   :floatconv,
            (DBF.LONG,DBF.DOUBLE)  :floatconv,
            (DBF.DOUBLE,DBF.STRING):store_none,
            (DBF.DOUBLE,DBF.INT  ) :intconv,
            (DBF.DOUBLE,DBF.ENUM)  :floatconv,
            (DBF.DOUBLE,DBF.CHAR)  :intconv,
            (DBF.DOUBLE,DBF.LONG)  :intconv,
           }

def dbr_convert_meta_value(from_dbf, to_dbf):
    return _converter_meta.get((from_dbf, to_dbf), _noop)
