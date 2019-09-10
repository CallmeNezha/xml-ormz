"""
# Convert xml into class definitions
#
# Copyright (C) 2019 ZIJIAN JIANG
"""

import os
import argparse
from typing import Union, Optional, List
from collections import defaultdict

from lxml import etree
from ..crawler.common import strip_xpath_index, read_xml_without_namespace
from ..orm.field import StringField, IntegerField, FloatField



class GenericFieldMatcher(object):
    __slots__ = [ 'fieldtype', 'is_optional' ]
    def __init__(self):
        
        self.fieldtype = IntegerField
        self.is_optional = False


    def match(self, value: Union[None, str, int, float]):

        if value is None:
            self.is_optional = True

        elif self.fieldtype == IntegerField:
            try:
                int(value)
            except ValueError:
                try:
                    float(value)
                except ValueError:
                    self.fieldtype = StringField
                else:
                    self.fieldtype = FloatField
            else:
                self.fieldtype = IntegerField
        
        elif self.fieldtype == FloatField:
            try:
                float(value)
            except ValueError:
                self.fieldtype = StringField
            else:
                self.fieldtype = FloatField

    def __str__(self):
        if self.is_optional:
            return f"Optional( {self.fieldtype.__name__}() )"
        else:
            return f"{self.fieldtype.__name__}()"

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("files", help="xml file to convert", type=str, nargs='+')
    parser.add_argument("-o", "--out", help="output model file", type=str, default="model.py")

    args = parser.parse_args()
    generate_pycode_from_xml(args.files, args.out)
    print(f"xml-ormz: Class template is written into file: {args.out}")


def generate_pycode_from_xml(xmlfiles: List[str], out="model.py"):
    for arg_file in xmlfiles:
        if not os.path.isfile(arg_file):
            print("File {} is not valid".format(arg_file))
            exit(-1)

    meta = get_meta_class(xmlfiles)
    with open(out, "w") as file:
        file.write( generate_pycode(meta) )
    

def generate_pycode(meta_class):
    from jinja2 import Template
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "template"), "r") as file:
        template = Template( file.read() )
        text = template.render(meta_class=meta_class)
        return text


def get_meta_class(files: List[str]):
    """
    Get meta class information of xml files of same type( same root tag )
    """
    cls_attributes = defaultdict( lambda: set( ) )
    cls_attributes_types = defaultdict( lambda: defaultdict( lambda: GenericFieldMatcher() ) )
    
    root_tag = set( )

    for fpath in files:
        tree = read_xml_without_namespace(fpath)
        root = tree.getroot()
        root_tag.add( root.tag )
    
        for e in root.iter(tag=etree.Element):
            
            elem = e
            path = tree.getpath(e)

            cls_name = strip_xpath_index(path).replace('/', '.')[1:]

            # not first time - compare to previous one
            if len(cls_attributes[ cls_name ]) != 0:
                for key in set( elem.keys() ) - cls_attributes[ cls_name ]:
                    cls_attributes_types[ cls_name ][ key ].match( None )
            
            cls_attributes[ cls_name ] |= set( elem.keys() )

            if len( cls_attributes[ cls_name ] ) == 0:
                cls_attributes_types[ cls_name ] = defaultdict( lambda: GenericFieldMatcher() )
            else:
                for key in cls_attributes[ cls_name ]:
                    attr = elem.get(key)
                    cls_attributes_types[ cls_name ][ key ].match(attr)
            
                
        
    if len(root_tag) != 1:
        raise RuntimeError(f"Different root type of xml files {files}.")


    # start composing hierachical meta information
    class_meta = {  }
    

    # build basic classes
    for k in sorted(cls_attributes_types.keys()):

        if k not in class_meta:
            
            class_meta[ k ] = { 
                "__name__": k.split(".")[-1],
                "__children__": [ ]
            }
    
    # build classes hierachy
    for cls_name in sorted(cls_attributes_types.keys()):
        cls_split = cls_name.split(".")
        if len(cls_split) > 1:
            parent = ".".join(cls_split[:-1])
            class_meta[ parent ][ "__children__" ].append( class_meta[ cls_name ] )

    # fillin fields
    for k, v in sorted(cls_attributes_types.items()):
        class_meta[ k ].update( v )

    # done
    root_tag = root_tag.pop()
    return class_meta[ root_tag ]

if __name__ == "__main__":
    main()