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
    >>> test=Enum(a=1, b=2, c=3)
    >>> test.a==1
    True
    >>> test.b==1
    False
    >>> test.a==test.b
    False
    >>> test.a==test.a
    True
    >>> test.a=2
    Traceback (most recent call last):
    ...
    AttributeError: Enumerations are readonly
    >>> print test.b
    Enum.b(2)
    """
    def __init__(self, prefix, **kwargs):
        for n,v in kwargs.iteritems():
            i=EnumItem(v)
            i._enum_name=prefix+'.'+n
            object.__setattr__(self, n, i)

    def __setattr__(self, k, v):
        raise AttributeError('Enumerations are readonly')

if __name__=='__main__':
    import doctest
    doctest.testmod()
