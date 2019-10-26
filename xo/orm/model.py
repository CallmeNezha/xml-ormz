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
    """ Meta class for **model class**.

    Meta of model used to parse meta model(xx_model.py) into class definitions.
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
    """Model class of python navtive class for xml element.

    Model class is native **python class** which defines element class, attributes corresponding to xml elements.

    For example:

        Xml File - literatures.xml:
        -------------
        <Author name="Jack">
            <Book name="XML tutorial" year="1992" ISBN="1928-01832">
            <Book name="Python tutorial" ISBN="7629-37669">
        </Author>

        Python model - literature_model.py:
        -------------
        class Author(Model):
            name = StringField()
            class Book(Model):
                name = StringField()
                year = Optional(IntegerField())
                ISBN = StringField(r=r'^\d{4}-\d{5}$')
                __count__ = (1,) # At least 1 book, or you will not be an author.

        Python script - main.py:
        -------------
        from xo.spider import XmlMapper
        from literature_model import Author

        obj_map = XmlMapper("literatures.xml", Author)
        # obj_map: Key is Xpath(which is unique), Value is instance of python object
        # {
        #   "Author": <object Class Author>,
        #   "Author/Book[1]": <object Class Book>, # In Xpath syntax, index is begin with 1 not zero.
        #   "Author/Book[2]": <object Class Book>
        # }

        obj_map["Author"].name 
        # returns: "Jack"
        obj_map["Author"].getChildren()[0].name 
        # returns: "XML tutorial"
        obj_map["Author"].getChildren()[0].year
        # returns: 1992
        obj_map["Author"].getChildren()[1].year
        # returns: None

    """
    def __init__(self, **kwargs):
        """Initialize a model with a keyword arguments of key:value of attribute:value

        Notice that if you don't supply *required* attributes with proper values , this initialization process will raise `AttributeError`.
        *Optional* attributes are OK be ignored.

        Args:
            kwargs: Keyword arguments of key:value of attribute:value.

        Returns:
            An instance with *required* attributes been properly assigned.

        Raises:
            AttributeError: Wrong attribute type or wrong attrute value which not passing **constraints**
        """

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
                    # set default value
                    kwargs[k] = v.default
                elif type(kwargs[k]) == type(None) and isOptional:
                    # user set this to None explicity
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
        """
        Returns:
            Parent class name.
        """
        parentclass_qualname = cls.getParentClassQualName()
        if parentclass_qualname:
            # return parent class `name`
            return parentclass_qualname.split(".")[-1]
        else:
            # not having parent
            return None

    @classmethod
    def getClassName(cls) -> str:
        """
        Returns:
            Class name of this model.
        """
        return cls.__name__

    @classmethod
    def getClassQualName(cls) -> str:
        """
        Returns:
            Class qual name of this model.
        """
        return cls.__qualname__

    @classmethod
    def getParentClassQualName(cls) -> typing.Optional[str]:
        """
        Returns:
            Parent class qual name.
        """
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
        """
        Returns:
            All child **classes** of this class.
        """
        return cls.__childclasses__ [:]

    @classmethod
    def isChildClass(cls, child:type) -> bool:
        """Check if `child` class is this model class's child.

        Args:
            child: Type of child.

        Returns:
            Bool value of validation.
        """
        if inspect.isclass(child):
            return child in cls.getChildClasses()
        else:
            raise ValueError(f'Invalid "child" parameter for classmethod isChildClass(): "{child}"')

    @classmethod
    def getField(cls, key:str):
        """Get `Field` of attribute with `key`.

        Notice:
            Don't mess `Field` with value of attribute, 
            `Field` is meta information which defines what kind of this attribute will be, and value is the value.

        Args:
            key: Key string of this attribute.
        
        Returns:
            `Field` of this attribute.
        """
        return cls.__mappings__.get(key, None)

    @classmethod
    def getFieldItems(cls):
        """Get `Field`s of all attributes of this model.

        Notice:
            Don't mess `Field` with value of attribute, 
            `Field` is meta information which defines what kind of this attribute will be, and value is the value.

        Returns:
            `Field`s of all all attributes of this model.
        """
        return cls.__mappings__.items()

    @staticmethod
    def is_valid_number(num: int, count: Union[int,Tuple[int,int]]) -> bool:
        """*Internal* number validation method.

        If count is `int` check if num == count.
        If count is `Tuple[int,int]` check if count[0] <= num <= count[1].

        Args:
            num: Number to validate.
            count: Number or range of number.

        Returns:
            Bool value of validation.
        
        Raises:
            RuntimeError: inproperly usage.
        """
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
        """*Internal* setter method.
        """

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

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(id(self))==hash(id(other))
        else:
            return False         

    def getAttr(self, key:str) -> typing.Optional[Union[str,int,float,object,List[object]]]:
        """Return attribute's value.

        Args:
            key: Key of attribute.

        Returns:
            Value of attribute.
        """
        return getattr(self, key, None)

    def setAttr(self, key:str, value:typing.Optional[Union[str,int,float,object,List[object]]]):
        """Set attribute's value.

        Notice if you set attribute with wrong type, this function will *raise error*.

        Args:
            key: Key of attribute.
            value: Value of attribute.

        Raises:
            AttributeError: Raise as `__setattr__` does
        """
        try:
            setattr(self, key, value)
        except AttributeError as e:
            raise e

    def getParent(self) -> typing.Optional['Model']:
        """Return parent if it exists.
        """
        if self.getParentClassName() is None:
            return None
        else:
            return getattr(self, f'__parent{self.getParentClassName()}')

    def setParent(self, parent:'Model'):
        """Set parent of this object. Also parent will be set to `parent`.

        Args:
            parent: Parent

        Raises:
            RuntimeError: If parent's model is not this model's parent, runtime eror will raise,
            if parent's childs' number is exceeding `__count__` constraint, runtime error will raise.
        """
        if not parent.isChildClass(self.__class__):
            raise RuntimeError(f'Can\'t assign parent of wrong type, "{self.getClassQualName()}" is not childclass of "{parent.getClassQualName()}"')

        self.removeFromParent()
        setattr(self, f'__parent{self.getParentClassName()}', parent)
        getattr(parent, f'__child{self.getClassName()}').append(self)

        if not self.is_valid_number( len( getattr(parent, f'__child{self.getClassName()}') ), self.__count__  ):
            raise RuntimeError(f'Can\'t append child, model count exceeding constaint "{self.getClassQualName()}" count expect {self.__class__.__count__}.')

    def removeFromParent(self):
        """Remove this object from it's current parent. Also parent will be set to none.

        Raises:
            RuntimeError: If this object is root, runtime error will raise, if it has no parent currently it's OK.
        """
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
        """Apprent child to this object. Also childn's parent will be set to this.

        Raises:
            RuntimeError: If `child` model is not child of this model, runtime error will raise.
        """
        if not self.isChildClass(child.__class__):
            raise RuntimeError(f'Can\'t append child of wrong type, "{child.getClassQualName()}" is not childclass of "{self.getClassQualName()}"')

        child.setParent(self)

    def removeChild(self, child:'Model'):
        """Remove child from this object. Also childn's parent will be set to none.
        
        Raises:
            RuntimeError: If `child` is actually not child of this object, runtime error will raise.
        """
        if child.getParent() != self:
            raise RuntimeError(f'Can\'t remove object which is not child of this parent')
        
        child.removeFromParent()

    def removeChildren(self):
        """Remove all children from this object. Also children's parent will be set to none.
        """
        for child in self.getChildren():
            child.removeFromParent()
        #endfor

    def getChildrenIter(self):
        """Return children iterator.
        """
        return chain.from_iterable( [ getattr(self, f'__child{childcls.getClassName()}') for childcls in self.getChildClasses() ] )

    def getChildren(self):
        """Return children list.
        """
        return list( self.getChildrenIter() )
    
    def toElement(self):
        """Convert object into etree.Element
        """
        return toElement(self)
    
        