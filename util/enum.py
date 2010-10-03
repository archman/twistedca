# -*- coding: utf-8 -*-

"""
Yet another python enumerated class
"""

__all__=['Enum']

class EnumItem(int):
    _enum_name="<Unknown>"
    def __str__(self):
        return '%s(%d)'%(self._enum_name,self)

class Enum(object):
    """
    An enumerated type with C-like arithmatic properties.

    >>> test=Enum('test.', a=1, b=2, c=0)
    >>> test.a==1
    True
    >>> test.b==1
    False
    >>> test.a==test.b
    False
    >>> test.a==test.a
    True
    >>> test.c==None
    False
    >>> (None or test.c) is test.c
    True
    >>> (test.c or None) is test.c
    False
    >>> test.a=2
    Traceback (most recent call last):
    ...
    AttributeError: Enumerations are read-only
    >>> print test.b
    test.b(2)
    >>> print test
    test.: a c b
    """
    def __init__(self, prefix, **kwargs):
        object.__setattr__(self,'_prefix',prefix)
        object.__setattr__(self,'_enums',{})
        for n,v in kwargs.iteritems():
            i=EnumItem(v)
            i._enum_name=prefix+n
            object.__setattr__(self, n, i)
            self._enums[n]=i

    def fromString(self, s):
        """
        Search list of enums to find matching string
        or None.
        
        >>> X=Enum('X.', A=0, B=1, C=2)
        >>> X.fromString('A') is X.A
        True
        >>> X.fromString('B') is X.B
        True
        >>> X.fromString('Q') is None
        True
        """
        for n,v in self._enums.iteritems():
            if n==s:
                return v
        try:
            val=int(s)
            for n,v in self._enums.iteritems():
                if val==v:
                    return v
        except ValueError:
            pass
        return None

    def fromInt(self, i):
        """
        Cast from integer to enum
        
        >>> X=Enum('X.', A=0, B=1, C=2)
        >>> X.fromInt(1) is X.B
        True
        >>> X.fromInt(2) is X.C
        True
        >>> X.fromInt(43) is None
        True
        """
        for v in self._enums.itervalues():
            if v==i:
                return v
        return None

    def __setattr__(self, k, v):
        raise AttributeError('Enumerations are read-only')

    def __str__(self):
        from copy import copy
        r=self._prefix+':'
        for n in self._enums.iterkeys():
            r+=' '+n
        return r

if __name__=='__main__':
    import doctest
    doctest.testmod()
