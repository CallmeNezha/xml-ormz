from .field import Field


import re
from typing import Union, List


class ForeignKeyField(object):
    """
    Foreign Key Field
    """
    def __init__(self, cls:Union[str, List[str]], name=None, *, finder=None):
        self.name = name
        self.column_type = cls
        self.finder = finder

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class ForeignKeyArrayField(ForeignKeyField):
    """
    Foreign Key Fields
    """
    def __init__(self, cls:str, name=None, *, finder=None):
        super().__init__(cls, name, finder=finder)


class StringField(Field):
    """
    Basic String Field
    """
    def __init__(self, name=None, primary_key=False, default=None, *, re=None):
        """
        Parameter:
            re - regular expression validator
        """
        super().__init__(name, str, primary_key, default)
        self.r = re

    def is_valid(self, string) -> bool:
        if self.r:
            return re.match(self.r, string) is not None
        else:
            return True


class IntegerField(Field):
    """
    Basic Integer Field
    """
    def __init__(self, name=None, primary_key=False, default=None, *, r=None):
        """
        Parameter:
            r  - function callback validator
        """
        super().__init__(name, int, primary_key, default)
        if r and not callable(r):
            raise TypeError("Parameter 'r' of IntergarField is not callable")
        self.r = r


    def is_valid(self, value) -> bool:
        if self.r:
            return self.r(value)
        else:
            return True


class FloatField(Field):
    """
    Basic Float Field
    """
    def __init__(self, name=None, primary_key=False, default=None, *, r=None):
        """
        Parameter:
            r  - function callback validator
        """
        super().__init__(name, float, primary_key, default)
        if r and not callable(r):
            raise TypeError("Parameter 'r' of FloatField is not callable")
        self.r = r

    def is_valid(self, value) -> bool:
        if self.r:
            return self.r(value)
        else:
            return True
    