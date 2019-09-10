import sys
import inspect
import functools
from itertools import chain

import typing
from typing import Union, Type, List, Tuple

from .. import logger
from .field import Field, Optional, ForeignKeyField, ForeignKeyArrayField
from .convert import toElement



class ModelMetaclass(type):
    """ Meta Class for model
    """
    def __new__(cls, name, bases, attrs):

        if name=='Model':
            return type.__new__(cls, name, bases, attrs)

        logger.debug( f'found model: {name}' )

        fields = [ ]
        childclasses = [ ]
        mappings = dict()

        # mappings
        for k, v in attrs.items():
            if isinstance(v, Field):
                logger.debug('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                fields.append(k)

            elif isinstance(v, Optional):
                logger.debug('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                fields.append(f"Optional({k})")
            elif isinstance(v, ForeignKeyField):
                logger.debug('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                fields.append(f"ForeignKeyField({k})")
            elif isinstance(v, ForeignKeyArrayField):
                logger.debug('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                fields.append(f"ForeignKeyArrayField({k})")

            elif inspect.isclass(v):
                # child classes
                logger.debug('  found childclass: %s' % v)
                childclasses.append(v)
            #endif

        for k in mappings.keys():
            attrs.pop(k)

        attrs['__mappings__'] = mappings 
        attrs['__fields__'] = fields
        attrs['__childclasses__'] = childclasses

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
    def __init__(self, **kwargs):

        qualname = self.__class__.__qualname__

        # Check attributes are valid
        for k, v in self.__mappings__.items():

            # Filed type or Optional(Field) type including:
            # StringField ; IntegerField ; FloatField
            if isinstance(v, Field):

                isOptional = type(v) == Optional

                if k not in kwargs and not isOptional:
                    raise AttributeError(f"'{qualname}': Missing required attribute: '{k}'")

                if k not in kwargs and isOptional:
                    pass

                elif type(kwargs[k]) == type(None) and isOptional:
                    pass

                elif type(kwargs[k]) != v.column_type:
                    raise AttributeError(f"'{qualname}': Wrong attribute '{k}' type, expect: '{v.column_type.__name__}', got: '{type(kwargs[k])}'")

                elif v.is_valid(kwargs[k]) == False:
                    raise AttributeError(f"'{qualname}': Attribute error, failed at attribute '{k}' constraint '{v.r}', got: '{kwargs[k]}'")

            
            # ForeignKeyField ;
            elif type(v) == ForeignKeyField:
                """
                It will be assigned at finder runtime
                """
                pass
            
            # ForeignKeyArrayField ;
            elif type(v) == ForeignKeyArrayField:
                """
                It will be assigned at finder runtime
                """
                pass
        #!for 

        remains = kwargs.keys() - ( set(self.__mappings__.keys()).union( { 'text' } ) )

        if len(remains) > 0:
            logger.warning(f"'{qualname}': Assigning undefined attributes: '{remains}'.")



        super(Model, self).__init__(**kwargs)

        #--------- assign __parent{Class}, __child{Class} attributes ---------#

        qualname_splits = qualname.split(".")

        if len(qualname_splits) > 1:
            # have parent
            parent_classname = qualname_splits[-2]
            setattr(self, f'__parent{parent_classname}', None) # place holder
        else:
            #root and not assign __parent{Class} attribute
            pass
        
        for childclass in self.__class__.__childclasses__:
            setattr(self, f'__child{childclass.getClassName()}', [ ])

        #--------- ! assign __parent{Class}, __child{Class} attributes ---------#

    @classmethod
    def getParentClassName(cls) -> typing.Optional[str]:
        parentclass_qualname = cls.getParentClassQualName()
        if parentclass_qualname:
            # return parent class name
            return parentclass_qualname.split(".")[-1]
        else:
            # not having parent
            return None

    @classmethod
    def getParentClassQualName(cls) -> typing.Optional[str]:
        qualname = cls.getClassQualName()
        qualname_split = qualname.split(".")
        if len( qualname_split ) > 1:
            # return parent name
            return ".".join(qualname_split[:-1])
        else:
            # not having parent
            return None

    @classmethod
    def getChildClasses(cls) -> List[type]:
        return cls.__childclasses__ [:]

    @classmethod
    def isChildClass(cls, child:type) -> bool:
        if inspect.isclass(child):
            return child in cls.getChildClasses()
        else:
            raise ValueError(f'Invalid "child" parameter for classmethod isChildClass(): "{child}"')

    @classmethod
    def getField(cls, key):
        return cls.__mappings__.get(key, None)

    @classmethod
    def getFieldItems(cls):
        return cls.__mappings__.items()

    @classmethod
    def getClassName(cls):
        return cls.__name__

    @classmethod
    def getClassQualName(cls):
        return cls.__qualname__

    @staticmethod
    def is_valid_number(num: int, count: Tuple[int,int]) -> bool:
        if type(count) == int:
            return num == count
        elif type(count) == tuple:
            return count[0] <= num <= count[1]
        else:
            raise RuntimeError("Probably a bug here. Please contact developer.")

    def __str__(self):
        return f"<class {self.__class__.__qualname__}>: {dict(self.items())}"
    
    def __repr__(self):
        return f"<class {self.__class__.__qualname__}>"

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{self.getClassQualName()}' object has no attribute '{key}'")

    def __setattr__(self, key, value):

        # check 
        field = self.getField(key)

        if type(field) == ForeignKeyField:
            if value!= None and type(value).__qualname__ not in field.column_type:
                raise AttributeError(f"'{self.__class__.__qualname__}': Wrong attribute '{key}' type, got '{type(value).__qualname__}', expect '{field.column_type}'.")

        elif type(field) == ForeignKeyArrayField:
            if type(value) != list:
                raise AttributeError(f"'{self.__class__.__qualname__}': Wrong attribute '{key}' type, got '{type(value).__qualname__}', expect 'List({field.column_type})'")
            
            else:
                wrongs = [ v for v in value if type(v).__qualname__ not in field.column_type ]
                if len( wrongs ) > 0:
                    raise AttributeError(f"'{self.__class__.__qualname__}': Wrong attribute '{key}' type, got '{wrongs}', expect 'List({field.column_type})'")

        elif isinstance(field, Field):
            if type(value) is not field.column_type:
                raise AttributeError(f"'{self.__class__.__qualname__}': Wrong attribute '{key}' type, got '{type(value)}', expect '{field.column_type}'.")

        else:
            # logger.warning(f"'{self.__class__.__qualname__}': Assign extra attribute '{key}' to object. Please notice.")
            pass

        self[key] = value

    def getAttr(self, key):
        return getattr(self, key, None)

    def setAttr(self, key, value):
        setattr(self, key, value)

    def getAttrOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logger.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    def getParent(self):
        if self.getParentClassName() is None:
            return None
        else:
            getattr(self, f'__parent{self.getParentClassName()}')

    def setParent(self, parent:'Model'):
        if not parent.isChildClass(self.__class__):
            raise RuntimeError(f'Can\'t assign parent of wrong type, "{self.getClassQualName()}" is not childclass of "{parent.getClassQualName()}"')

        self.removeFromParent()
        setattr(self, f'__parent{self.getParentClassName()}', parent)
        getattr(parent, f'__child{self.getClassName()}').append(self)

        if not self.is_valid_number( len( getattr(parent, f'__child{self.getClassName()}') ), self.__count__  ):
            raise RuntimeError(f'Can\'t append child, model count exceeding constaint "{self.getClassQualName()}" count expect {self.__class__.__count__}.')

        
        
    def removeFromParent(self):
        parent_classname = self.getParentClassName()
        if parent_classname is None:
            raise RuntimeError(f'root class "{self.getClassQualName()}" has no parent.')

        if getattr(self, f'__parent{parent_classname}') is not None:
            parent_obj = getattr(self, f'__parent{parent_classname}')
            getattr(parent_obj, f'__child{self.getClassName()}').remove(self)
            setattr(self, f'__parent{parent_classname}', None)
        else:
            #TODO: Should we warning here?
            pass

    
    def appendChild(self, child:'Model'):
        if not self.isChildClass(child.__class__):
            raise RuntimeError(f'Can\'t append child of wrong type, "{child.getClassQualName()}" is not childclass of "{self.getClassQualName()}"')

        child.setParent(self)


    def getChildrenIter(self):
        return chain.from_iterable( [ getattr(self, f'__child{childcls.getClassName()}') for childcls in self.getChildClasses() ] )

    def getChildren(self):
        return list( self.getChildrenIter() )
    
    def removeChild(self, child:'Model'):
        if child.getParent() != self:
            raise RuntimeError(f'Can\'t remove object which is not child of this parent')
        
        child.removeFromParent()

    def removeChildren(self):
        for child in self.getChildren():
            child.removeFromParent()
        #endfor

    def toElement(self):
        """
        convert object into etree.Element
        """
        return toElement(self)
    
        