# -*- coding: utf-8 -*-

import logging
import xcode

_log=logging.getLogger('TwCA.pvd')

ELEMMASK=0x0F
CLSMASK=0xF0

SCALAR=0x00
SCALARARRAY=0x10
STRUCT=0x20
STRUCTARRAY=0x30

BOOL=0x00
BYTE=0x01
SHORT=0x02
INT=0x03
LONG=0x04
FLOAT=0x05
DOUBLE=0x06
STRING=0x07

BOOLARRAY=BOOL|SCALARARRAY
BYTEARRAY=BYTE|SCALARARRAY
SHORTARRAY=SHORT|SCALARARRAY
INTARRAY=INT|SCALARARRAY
LONGARRAY=LONG|SCALARARRAY
FLOATARRAY=FLOAT|SCALARARRAY
DOUBLEARRAY=DOUBLE|SCALARARRAY
STRINGARRAY=STRING|SCALARARRAY


_valueNames={
    'bool':BOOL,
    'char':BYTE,
    'short':SHORT,
    'int':INT,
    'long':LONG,
    'float':FLOAT,
    'double':DOUBLE,
    'string':STRING,
}
for k, v in _valueNames.items():
    _valueNames[k+'[]']=v|SCALARARRAY
_valueNamesR={}
for v, k in _valueNames.iteritems():
    _valueNamesR[k]=v

class FieldDesc(object):    
    def __init__(self, id=None, bit=0,
                 name='<unnamed>', type=xcode.NULLTYPE,
                 children=None):
        self.id=id # set for top-level structures
        self.bit=bit
        self.name=name
        self.type=type
        self.children=children

    def __eq__(self, other):
        """Recursive comparison
        """
        if other is None:
            return False
        if self is other:
            return True
        for tok in ['id', 'bit', 'name', 'type', 'count']:
            if not hasattr(other, tok) or \
                    getattr(self, tok)!=getattr(other,tok):
                return False
        if not hasattr(other, 'children'):
            return False
        if (self.children is None) ^ (other.children is None):
            return False
        if self.children is not None:
            if len(self.children) != len(other.children):
                return False
            for s, o in zip(self.children, other.children):
                if s!=o:
                    return False
        return True

    def __unicode__(self):
        """
        >>> FieldDesc(name='test', type=SCALAR|INT)
        test:int
        """
        s=str()
        if self.id is not None:
            s+='<%d> '%self.id
        s+=self.name
        if self.bit>0:
            s+='[%d]'%self.bit
        s+=':'
        cls=self.type&CLSMASK
        if cls==SCALAR or cls==SCALARARRAY:
            s+='%s'%_valueNamesR[self.type&ELEMMASK]
        elif cls==STRUCTARRAY:
            s+='['
            
        if cls==STRUCT or cls==STRUCTARRAY:
            s+='{ '
            s+=', '.join([unicode(c) for c in self.children])
            s+=' }'
        if cls==STRUCTARRAY:
            s+=']'
        return s

    def __str__(self):
        x=unicode(self)
        return x.encode('ascii')
    def __repr__(self):
        return unicode(self)
            

class FieldContext(object):
    """Caching store of FieldDesc
    """
    __FC=FieldDesc

    def __init__(self):
        self.__cache={}
        self.__nextid=1

    def getID(self):
        id=self.__nextid
        self.__nextid+=1
        assert id<=0xffff, 'Too many structures in this context'
        return id

    def decode(self, raw):
        """Take raw byte string and return (remaining string,FieldDesc)
        """
        assert len(raw)>0
        
        ftype=raw[0]
        
        if ftype==xcode.NULLTYPE:
            return self.__FC()

        _,tid=xcode.deStructDescID(raw[1:3])
        obj=self.__cache.get(tid)

        if ftype==xcode.ONLYID:
            if obj is None:
                raise RuntimeError('Message contains unknown Type Code %d'%tid)
            return obj

        elif ftype==xcode.FULLID:
            raw, ftype, name=xcode.deFieldDesc(raw[3:])
            assert ftype==STRUCT or ftype==STRUCTARRAY
            raw, memcount=xcode.deSize(raw)
            
            c=[]
            for i in xrange(memcount):
                mtype=raw[0]
                if mtype in [xcode.FULLID, xcode.ONLYID, xcode.NULLTYPE]:
                    raw, cfld = self.decode(raw)
                    c.append(cfld)
                else:
                    raw, ctype, cname = xcode.deFieldDesc(raw)
                    c.append(FieldDesc(name=cname, type=ctype))
                    
            obj2=FieldDesc(name=name, type=ftype, children=c)
            if obj==obj2:
                _log.info("Server resent duplicate FieldDesc")
            elif obj is not None and obj!=obj2:
                raise RuntimeError("Server reused Type Code %d without telling us!"%tid)
            else:
                self.__cache[tid]=obj2
            return raw, obj2

    def encode(self, desc=None, id=None):
        """Given either a type code ID and FieldDesc
        Produce a byte string
        """
        if id is None:
            if desc.id is not None:
                id=desc.id
            else:
                desc.id= id= self.getID()

        if id not in self.__cache:
            assert desc is not None, "Must provide FieldDesc if ID not cached"
            raw=xcode.enStructDesc(id)+xcode.enFieldDesc(desc.type, desc.name)
            self.__cache[id]=desc
            
            if desc.type==STRUCTARRAY:
                raw+=xcode.enSize(0) #TODO: What is "structure name"?
            
            if desc.children is not None:
                raw+=xcode.enSize(len(desc.children))
                for c in desc.children:
                    if c.type in [STRUCT, STRUCTARRAY]:
                        _, enc=self.encode(desc=c)
                        raw+=enc
                    else:
                        raw+=xcode.enFieldDesc(c.type, c.name)

        else:
            raw=xcode.enStructDescID(id)

        return id, raw

    def decodeDesc(self, raw):
        pass


def createStruct(name,*args,**kws):
    """createStruct('name', memname='type', other={}, last=[{}])
    createStruct('name', ('memname','type'), ('other',{}), ('last',[{}]) ) 
    
    Create a FieldDesc describing a structure
    
    Member names are taken from argument names.
    values can be 'bool', 'byte', 'short', 'int', 'long',
    'float', 'double', 'string', or any of these with the suffix
    '[]' to indicate an array (ie. 'short[]').
    
    Values can also be a dictionary which defines a sub-structure,
    or an list (length 1) containing a structure to define
    a sub-structure array.

    >>> fld=createStruct('name', value='int', severity='short')
    >>> fld.children
    [severity:short, value:int]
    >>> unicode(fld)
    u'name:{ severity:short, value:int }'
    >>> fld.name
    'name'
    >>> fld.type==STRUCT
    True
    >>> fld=createStruct('name', ('value','int'), ('severity','short'))
    >>> fld.children
    [value:int, severity:short]
    """
    from itertools import chain
    c=[]
    for ent in chain(iter(args), kws.iteritems()):
        if isinstance(ent, tuple):
            # ('member name', XX)
            mname, val = ent
            if isinstance(val, list):
                if isinstance(val[0], list):
                    # ordered struct array
                    assert len(val)==1
                    s=createStruct(mname, *val[0])
                    s.type=STRUCTARRAY

                elif isinstance(val[0], dict):
                    # unordered struct array
                    assert len(val)==1
                    s=createStruct(mname, **val[0])
                    s.type=STRUCTARRAY

                else:
                    # ordered struct
                    s=createStruct(mname, *val)
                
            elif isinstance(val, dict):
                # unordered struct
                s=createStruct(mname, **val)
    
            elif isinstance(val, str):
                # leaf field
                ftype=_valueNames.get(val)
                s=FieldDesc(name=mname, type=ftype)

            elif isinstance(val, FieldDesc):
                raise AttributeError('FieldDesc already has a name')

            else:
                raise AttributeError('Unknown argument: (%s) %s=%s'% \
                    (type(val),mname,val))

        elif isinstance(ent, FieldDesc):
            # pre-computed
            s=ent

        else:
            raise AttributeError('Unknown argument: (%s) %s'%(type(ent),ent))

        c.append(s)
            
        
    return FieldDesc(name=name, type=STRUCT, children=c)

def _test():
    import doctest
    doctest.testmod()

if __name__=='__main__':
    _test()
