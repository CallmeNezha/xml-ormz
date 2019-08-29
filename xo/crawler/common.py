from lxml import etree
import re

from typing import Type, List
import inspect

import logging

# ==========================================
#   File Utilities
# ==========================================

def xml2tree(path: str) -> etree._Element:
    with open(path, "r", encoding="utf-8") as file:
        tree = etree.parse(file)
        
    root = tree.getroot()
    if not etree.iselement(root):
        raise Exception("error")
    return tree

def xml2file(root: etree._Element, path: str):
    with open(path, mode='wb') as file:
        parser = etree.XMLParser(encoding='utf-8',remove_blank_text=True)
        string = str(etree.tostring(root, pretty_print=True, encoding='unicode'))
        string = string.encode('utf-8')
        root = etree.XML(string, parser)
        output = b"<?xml version=\"1.0\" encoding=\"utf-8\"?>" + b"\n" + etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=False)
        file.write(output)

def strip_xpath_index(xpath: str):
    """
    /A/B[1]/C[2] --> /A/B/C
    """
    return re.sub("\[\d+\]", "", xpath)


def get_all_class_types(cls: Type) -> List[Type]:
    """
    Get all nested class type from class given

    Parameters:
        cls - class type object

    Return:
        list of nested class
    """
    cls_list = [cls]

    def inner_classes_list(_cls, _cls_list):
        inner_class = [cls_attribute for cls_attribute in _cls.__dict__.values() if inspect.isclass(cls_attribute)]
        _cls_list += inner_class
        if len(inner_class):
            for ic in inner_class:
                inner_classes_list(ic, _cls_list)
        else:
            return
    # recursively extract
    inner_classes_list(cls, cls_list)

    return cls_list

def install_coloredlogs(level='INFO'):
    logger = logging.getLogger()
    try:
        import coloredlogs
        coloredlogs.install(level=level, logger=logger)
    except ImportError:
        logging.info("xml-ormz: coloredlogs not installed using plain logging style.")
    return logger