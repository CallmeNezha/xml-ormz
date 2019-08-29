import logging
from .field import Field, Optional
from .basicfields import ForeignKeyField, ForeignKeyArrayField
import functools
import sys

logging = logging.getLogger(__name__)

class ModelMetaclass(type):
    """
    Meta Class
    """
    def __new__(cls, name, bases, attrs):
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError("Duplicate primary key for field: '%s'" % k)
                    primaryKey = k
                else:
                    fields.append(k)
            elif isinstance(v, Optional):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                fields.append(f"Optional({k})")
            elif isinstance(v, ForeignKeyField):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                fields.append(f"ForeignKeyField({k})")
            elif isinstance(v, ForeignKeyArrayField):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                fields.append(f"ForeignKeyArrayField({k})")
            #endif
        if not primaryKey:
            #TODO: @nezha add default counting primary key
            pass
            # raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings 
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields

        # set count constraints
        if '__count__' in attrs:
            count = attrs['__count__']
            if type(count) == int and count > 0:
                attrs['__count__'] = count
            elif type(count) == tuple and len(count) == 1:
                attrs['__count__'] = (count[0], sys.maxsize)
            elif type(count) == tuple and len(count) == 2 and\
                  type(count[0]) == int and count[0] >= 0 and\
                  type(count[1]) == int and count[0] < count[1]:
                attrs['__count__'] = count
            
            else:
                raise ValueError("'__count__' attribute of model only expect integer > 0 or tuple of integer")
        else:
            attrs['__count__'] = (0, sys.maxsize)
                

        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    """
    Model Class
    """
    def __init__(self, **kw):

        qualname = self.__class__.__qualname__
        # Check attributes are valid
        for k, v in self.__mappings__.items():

            # Filed type or Optional(Field) type
            if isinstance(v, Field) or type(v) == Optional:
                isOptional = type(v) == Optional
                if k not in kw and not isOptional:
                    raise AttributeError(f"'{qualname}': Missing required attribute: '{k}'.")
                if k not in kw and isOptional:
                    pass
                elif type(kw[k]) == type(None) and isOptional:
                    pass
                elif type(kw[k]) != v.column_type:
                    raise AttributeError(f"'{qualname}': Wrong attribute type, expect: '{v.column_type.__name__}', got: '{type(kw[k])}'.")
                elif v.is_valid(kw[k]) == False:
                    raise AttributeError(f"'{qualname}': Attribute error, failed at attribute '{k}' constraint '{v.r}', got: '{kw[k]}'")

            # (2019-08-28 15:54:06) remove ArrayField @Nezha
            # # ArrayField type
            # elif isinstance(v, ArrayField):
            #     if k not in kw:
            #         raise AttributeError(f"'{qualname}': Missing required attribute: '{k}'.")
            #     for e in kw[k]:
            #         if type(e) != v.column_type:
            #             raise AttributeError(f"'{qualname}': Wrong attribute type, expect: '{v.column_type.__name__}', got: '{type(e)}' in array.")
        #!for 

        remains = kw.keys() - ( set(self.__mappings__.keys()).union( { 'text' } ) )
        if len(remains) > 0:
            logging.warning(f"'{qualname}': Assigning undefined attributes: '{remains}'.")

        super(Model, self).__init__(**kw)
       

    @classmethod
    def getField(cls, key):
        return cls.__mappings__.get(key, None)

    @classmethod
    def getFields(cls):
        return cls.__mappings__.items()

    def __str__(self):
        return f"<class {self.__class__.__qualname__}>: {dict(self.items())}"
    
    def __repr__(self):
        return f"<class {self.__class__.__qualname__}>"

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

