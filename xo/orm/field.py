import re
from typing import Union, List
from abc import ABC, abstractmethod


class Field(ABC):
    """ Base field type

    Attributes:
        name: field name
        column_type: field type; string integar float or something else
        primary_key: currently not used, but reserved for later useage
        default: currently not used, but this feature will coming soon
        r: regular expression `r'{..}'` or regularize function `lambda x: 1 < x < 100`

    Notice:
        If you want add additional field, please implement abstract method is_valid()
    """
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
        self.r = None

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type.__name__, self.name)

    @abstractmethod
    def is_valid(self, *args, **kwargs):
        """ Abstract Method must be implemented by subclass """
        return True



class Optional(object):
    """ Optional type is a wrapper for Field

    Attributes:
        field: field that is optional(can be `None`)
    """
    def __init__(self, field: Field):

        if not isinstance(field, Field):
            raise TypeError("Expect 'Field' type")
        
        if field.primary_key == True:
            raise RuntimeError("Optional field is primary key")

        self.field = field

        self.__setattr__ = self.__setattr_delegate__
    

    def __getattr__(self, key):
        try:
            return getattr(self.field, key)
        except KeyError:
            raise AttributeError(r"'Field' object has no attribute '%s'" % key)


    def __setattr_delegate__(self, key, value):
        """ Delegate field object
        """
        setattr(self.field, key, value)


    def __str__(self):
        return '<Optional(%s), %s:%s>' % (self.field.__class__.__name__, 
                                          self.field.column_type.__name__, 
                                          self.field.name)



# -------------- Builtin Fields --------------- #

class ForeignKeyField(object):
    """ Foreign Key Field

    Attributes:
        name: field name
        column_type: foreign key's class type, could be list of types
        finder: finder's usage see tutorial
    """
    def __init__(self, cls:Union[str, List[str]], name=None, *, finder=None):
        self.name = name
        self.column_type = cls
        self.finder = finder

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)



class ForeignKeyArrayField(ForeignKeyField):
    """ Foreign Key Fields

    
    """
    def __init__(self, cls:str, name=None, *, finder=None):
        super().__init__(cls, name, finder=finder)



class StringField(Field):
    """String Field

    Args:
        name: inherit from Field
        primary_key: inherit from Field
        default: inherit from Field
        r: regular expression
    """
    def __init__(self, name=None, primary_key=False, default=None, *, re=None):
        """
        Parameter:
            re: regular expression validator
        """
        super().__init__(name, str, primary_key, default)
        self.r = re

    def is_valid(self, string) -> bool:
        if self.r:
            return re.match(self.r, string) is not None
        else:
            return True



class IntegerField(Field):
    """ Integer Field

    Attributes:
        name: inherit from Field
        primary_key: inherit from Field
        default: inherit from Field
        r: regularize function
    """
    def __init__(self, name=None, primary_key=False, default=None, *, r=None):
        """
        Parameter:
            r: regularize function
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
    """ Float Field

    Attributes:
        name: inherit from Field
        primary_key: inherit from Field
        default: inherit from Field
        r: regularize function
    """
    def __init__(self, name=None, primary_key=False, default=None, *, r=None):
        """
        Parameter:
            r: regularize function
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

    