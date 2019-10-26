

import re
from itertools import chain
from collections import defaultdict
from typing import List, Dict, Tuple, Any
from urllib.parse import unquote 

from lxml import etree
from .. import logger

from .common import strip_xpath_index, get_all_class_types, read_xml_without_namespace
from ..orm.field import Field, Optional, FloatField, StringField, IntegerField, ForeignKeyField, ForeignKeyArrayField
from ..orm import Model



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



    # def paths_meta(self, xpaths:List[str]):
    #     """
    #     Get path meta information of all xpaths in one xml.

    #     Parameters:
    #         xpaths - xpaths starting from root
    #                    of all elements [ /A, /A/B[1], /A/B[1]/C ... ]
        
    #     Return:
    #         dict { xpath: is_multiple:bool }
    #     """
    #     is_multiple = defaultdict(lambda: False)
    #     # split index numbers
    #     prog = re.compile('.+\[(\d+)\]$')
    #     for x in xpaths:
    #         is_multiple[ strip_xpath_index(x) ] |= prog.match(x) is not None
    #     #endfor
    #     return is_multiple


class XmlLinker(object):
    """Linker of xml mappers, use user provide `finder` to link objects' relationships.

    """
    def __init__(self, orm_list:List[Dict[str,'Model']], model_cls_list:List[type]):
        """Initialiation of XmlLinker

        Args:
            orm_list: List of `orm_map` returned from `XmlMapper.Parse`.
            model_cls_list: List of all `Model` classes.
        """
        self.orm_list = orm_list
        all_cls = chain.from_iterable( [ [ cls for cls in get_all_class_types(model_cls) ] for model_cls in model_cls_list ] )
        
        for cls in all_cls:
            logger.debug(f"Initializing class '{cls.__qualname__}'...")

            for name, field in cls.getFieldItems():
                if type(field) not in [ ForeignKeyField, ForeignKeyArrayField ]:
                    continue

                # initialize
                logger.debug(f"  - field '{name}' finder.")
                if field.finder is None:
                    raise RuntimeError(f"ForeignKeyField '{name}' of '{cls.__qualname__}' has no finder assigned.")
                elif not callable(field.finder):
                    raise RuntimeError(f"ForeignKeyField '{name}' of '{cls.__qualname__}' has finder is not callable.")

    def set_env(self, env_vars):
        """Set environment variables that `finder`s (first argument of `finder` function call) needed.

        Args:
            env_vars: Dictionary of variables.
        """
        self.env_vars = env_vars

    def link(self):
        """Call every `finder` to find object reference to assign `ForignKey` field of model.
        """
        models = chain.from_iterable( [ orm.values() for orm in self.orm_list ] )
        for model in models:
            for name, field in model.getFieldItems():
                if type(field) == ForeignKeyField:
                    filled = field.finder(self.env_vars, model)

                    if filled == None:
                        logger.warning(f"ForeignKeyField '{name}' of '{model.__class__.__qualname__}' find nothing for '{model}'.")

                    setattr(model, name, filled)
                    
                # array
                elif type(field) == ForeignKeyArrayField:
                    filled = field.finder(self.env_vars, model)
                    
                    if filled == None:
                        logger.warning(f"ForeignKeyField '{name}' of '{model.__class__.__qualname__}' find nothing for '{model}'")
                        filled = [ ]

                    if len(filled) == 0:
                        logger.warning(f"ForeignKeyField '{name}' of '{model.__class__.__qualname__}' find nothing for '{model}'")
                
                    setattr(model, name, filled)

                

                        

    
