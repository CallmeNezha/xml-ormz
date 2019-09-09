
from lxml import etree
from .basicfields import StringField, FloatField, IntegerField
from .field import Optional

def toElement(model):
    """
    TODO: maybe rewrite it into none recursive callback will be better,
    Hope it never meets stack overflow...
    """
    elem = etree.Element(model.getClassName())
    for k, v in model.getFields():
        if type( v ) in [StringField, FloatField, IntegerField, Optional] and model.getAttr(k) is not None:
            elem.set( k, str ( model.getAttr( k ) ) ) 
    
    for childcls in model.getChildClasses():
        for child in getattr(model, f'child{childcls.getClassName()}'):
            elem.append( toElement(child) )

    return elem