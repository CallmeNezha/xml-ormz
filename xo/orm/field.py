

class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
        self.r = None

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type.__name__, self.name)

    def is_valid(self, *args, **kwargs):
        return True

class Optional(object):
    
    def __init__(self, field: Field):
        if not isinstance(field, Field):
            raise TypeError("Expect 'Field' type")
        if field.primary_key == True:
            raise RuntimeError("Optional field is primary key")
        self.field = field
        self.__setattr__ = self._setattr
    
    def __getattr__(self, key):
        try:
            return getattr(self.field, key)
        except KeyError:
            raise AttributeError(r"'Field' object has no attribute '%s'" % key)

    def _setattr(self, key, value):
        setattr(self.field, key, value)

    def __str__(self):
        return '<Optional(%s), %s:%s>' % (self.field.__class__.__name__, 
                                          self.field.column_type.__name__, 
                                          self.field.name)