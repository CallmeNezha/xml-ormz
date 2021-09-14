

import re
from itertools import chain
from collections import defaultdict
from typing import List, Dict, Tuple, Any
from urllib.parse import unquote 

from lxml import etree
from xo import logger

from xo.orm.common import strip_xpath_index, get_all_class_types, read_xml_without_namespace
from xo.orm.field import Field, Optional, FloatField, StringField, IntegerField, ForeignKeyField, ForeignKeyArrayField
from xo.orm import Model



class XmlMapper(object):
    """Xml Mapper to convert xml etree to model objects.
    """
    def __init__(self, xml:str, model_cls:type):
        """Initializtion of XmlMapper

        Args:
            xml: Xml file path.
            model_cls: `Model` class

        """
        self.xml = xml
        self.tree = read_xml_without_namespace(xml)
        self.model_cls = model_cls

    def parse(self):
        """
        Returns:
            Python native objects that converted from xml elements.

        Raises:
            RuntimeError: If root(xml type) is not expected or `__count__` constraints is vialated.
            ValueError: If attribute's value is not expected.

        """
        # xml elements
        tree = self.tree
        root = tree.getroot()

        # get class types
        model_cls = self.model_cls
        icls = {cls.__qualname__ : cls for cls in get_all_class_types(model_cls) }


        # check number of children count constraints
        for cls_name, cls in icls.items():
            splitted = cls_name.split('.')
            if len(splitted) < 1:
                raise RuntimeError("Doesn't has root.")
            elif len(splitted) == 1:
                pass
            elif len(splitted) > 1:
                parent_xpath, child_xpath = "/"+"/".join(splitted[:-1]), splitted[-1]
                for parent in tree.xpath(parent_xpath):
                    if not self.is_valid_number(len(parent.xpath(child_xpath)), cls.__count__):
                        raise RuntimeError(f"File {unquote(parent.base)}, line {parent.sourceline}, model count constaint error: '{cls_name}' count is {len(parent.xpath(child_xpath))}, expect: {cls.__count__}.")



        paths: List[str] = [tree.getpath(e) for e in root.iter(tag=etree.Element)]
        
        xcls = set([strip_xpath_index(p).replace('/', '.')[1:] for p in paths])

        # check consistance of model class and xml elements types
        if len(xcls - icls.keys()) > 0:
            raise RuntimeError(f"{unquote(root.base)}, xml element class {xcls - icls.keys()} is not defined in model.")
        elif len(icls.keys() - xcls) > 0:
            logger.debug(f"{unquote(root.base)}, class {icls.keys() - xcls} defined in model is not found in xml")

        # build mapped object related model
        obj_map = dict( )
        
        for e in root.iter(tag=etree.Element):
            elem = e
            path = tree.getpath(e)

            cls_name = strip_xpath_index(path).replace('/', '.')[1:]
            cls = icls[cls_name]

            assign_items = { }
            try:
                for k, v in elem.items():
                    field = cls.getField(k)
                    if type(field) == Optional:
                        field = field.field
                    if field is None:
                        logger.warning(f"Try to assign extra attribute '{k}' to undefined field of '{cls_name}', drop it.")
                        logger.warning(f"  - File {unquote(elem.base)}, line {elem.sourceline}")
                    elif type(field) == StringField:
                        assign_items[k] = v
                    elif type(field) == IntegerField:
                        assign_items[k] = int(v)
                    elif type(field) == FloatField:
                        assign_items[k] = float(v)
                    else:
                        raise RuntimeError(f"Unknown field type '{field}'")
                
                if elem.text:
                    assign_items["text"] = elem.text.strip()

            except ValueError:
                raise ValueError(f"File {unquote(elem.base)}, line {elem.sourceline}, error type of field '{k}' of '{cls}', got '{type(v)}', expect '{field}'.")
                    

            # create object of class
            obj = cls(**assign_items)
            obj_map[path] = obj


            # Append it to parent object and set its parent
            parent_elem = elem.getparent()
            if parent_elem is None:
                pass # root
            else:
                # has parent
                parent = obj_map[tree.getpath(parent_elem)]
                parent.appendChild(obj)


        #endfor
        return obj_map

    
    @staticmethod
    def is_valid_number(num: int, count: Tuple[int,int]) -> bool:
        if type(count) == int:
            return num == count
        elif type(count) == tuple:
            return count[0] <= num <= count[1]
        else:
            raise RuntimeError("Probably a bug here. Please contact developer.")



    
