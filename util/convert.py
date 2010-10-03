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
        return spec%val

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
            (DBF_STRING,DBF_INT)   :intconv,
            (DBF_STRING,DBF_FLOAT) :floatconv,
            (DBF_STRING,DBF_ENUM)  :chooseEnum,
            (DBF_STRING,DBF_CHAR)  :str_as_carray,
            (DBF_STRING,DBF_LONG)  :intconv,
            (DBF_STRING,DBF_DOUBLE):floatconv,
            (DBF_INT,DBF_STRING)   :intprint,
            (DBF_INT,DBF_FLOAT)    :floatconv,
            #(DBF_INT,DBF_ENUM)     :_noop,
            #(DBF_INT,DBF_CHAR)     :_noop,
            #(DBF_INT,DBF_LONG)     :_noop,
            (DBF_INT,DBF_DOUBLE)   :floatconv,
            (DBF_FLOAT,DBF_STRING) :floatprint,
            (DBF_FLOAT,DBF_INT)    :intconv,
            (DBF_FLOAT,DBF_ENUM)   :intconv,
            (DBF_FLOAT,DBF_CHAR)   :intprint,
            (DBF_FLOAT,DBF_LONG)   :intconv,
            #(DBF_FLOAT,DBF_DOUBLE) :_noop,
            (DBF_ENUM,DBF_STRING)  :printEnum,
            #(DBF_ENUM,DBF_INT)     :_noop,
            (DBF_ENUM,DBF_FLOAT)   :floatconv,
            #(DBF_ENUM,DBF_CHAR)    :_noop, #BUG: return char array?
            #(DBF_ENUM,DBF_LONG)    :_noop,
            (DBF_ENUM,DBF_DOUBLE)  :floatconv,
            (DBF_CHAR,DBF_STRING)  :carray_as_str,
            #(DBF_CHAR,DBF_INT)     :_noop,
            (DBF_CHAR,DBF_FLOAT)   :floatconv,
            #(DBF_CHAR,DBF_ENUM)    :_noop, #BUG: interpret as string?
            #(DBF_CHAR,DBF_LONG)    :_noop,
            (DBF_CHAR,DBF_DOUBLE)  :floatconv,
            (DBF_LONG,DBF_STRING)  :intprint,
            #(DBF_LONG,DBF_INT)     :_noop,
            (DBF_LONG,DBF_FLOAT)   :floatconv,
            #(DBF_LONG,DBF_ENUM)    :_noop,
            #(DBF_LONG,DBF_CHAR)    :_noop,
            (DBF_LONG,DBF_DOUBLE)  :floatconv,
            (DBF_DOUBLE,DBF_STRING):floatprint,
            (DBF_DOUBLE,DBF_INT  ) :intconv,
            #(DBF_DOUBLE,DBF_FLOAT) :_noop,
            (DBF_DOUBLE,DBF_ENUM)  :floatconv,
            (DBF_DOUBLE,DBF_CHAR)  :intconv,
            (DBF_DOUBLE,DBF_LONG)  :intconv,
           }
def dbr_convert_value(from_dbf, to_dbf):
    return _converter_value.get((from_dbf, to_dbf), _noop)

def store_zero(val, **kwargs):
    return 0

def store_none(val, **kwargs):
    return None

_converter_meta={
            (DBF_STRING,DBF_INT)   :store_zero,
            (DBF_STRING,DBF_FLOAT) :store_zero,
            (DBF_STRING,DBF_ENUM)  :store_zero,
            (DBF_STRING,DBF_CHAR)  :store_zero,
            (DBF_STRING,DBF_LONG)  :store_zero,
            (DBF_STRING,DBF_DOUBLE):store_zero,
            (DBF_INT,DBF_STRING)   :store_none,
            (DBF_INT,DBF_FLOAT)    :floatconv,
            (DBF_INT,DBF_CHAR)     :intprint,
            (DBF_INT,DBF_DOUBLE)   :floatconv,
            (DBF_FLOAT,DBF_STRING) :store_none,
            (DBF_FLOAT,DBF_INT)    :intconv,
            (DBF_FLOAT,DBF_ENUM)   :intconv,
            (DBF_FLOAT,DBF_CHAR)   :intprint,
            (DBF_FLOAT,DBF_LONG)   :intconv,
            (DBF_ENUM,DBF_STRING)  :store_none,
            (DBF_ENUM,DBF_FLOAT)   :floatconv,
            (DBF_ENUM,DBF_DOUBLE)  :floatconv,
            (DBF_CHAR,DBF_STRING)  :store_none,
            (DBF_CHAR,DBF_FLOAT)   :floatconv,
            (DBF_CHAR,DBF_DOUBLE)  :floatconv,
            (DBF_LONG,DBF_STRING)  :store_none,
            (DBF_LONG,DBF_FLOAT)   :floatconv,
            (DBF_LONG,DBF_DOUBLE)  :floatconv,
            (DBF_DOUBLE,DBF_STRING):store_none,
            (DBF_DOUBLE,DBF_INT  ) :intconv,
            (DBF_DOUBLE,DBF_ENUM)  :floatconv,
            (DBF_DOUBLE,DBF_CHAR)  :intconv,
            (DBF_DOUBLE,DBF_LONG)  :intconv,
           }

def dbr_convert_meta_value(from_dbf, to_dbf):
    return _converter_meta.get((from_dbf, to_dbf), _noop)
