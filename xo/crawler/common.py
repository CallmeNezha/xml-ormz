import re
import inspect
from typing import Type, List
from lxml import etree, objectify

# ==========================================
#   File Utilities
# ==========================================

def xml2tree(path: str) -> etree._Element:
    """Read etree from xml file.
    
    Args:
        path: Xml file path.
    
    Returns:
        Etree.

    Raises:
        IOError: Failed to read file.
        Exception: Bug
    """
    with open(path, "r", encoding="utf-8") as file:
        tree = etree.parse(file)
        
    root = tree.getroot()
    if not etree.iselement(root):
        raise Exception("error")
    return tree

def xml2file(root: etree._Element, path: str):
    """Write etree root to file.
    Args:
        root: Etree root element.
        path: File path to write.

    Raises:
        IOError: Failed to write file.
    """
    with open(path, mode='wb') as file:
        parser = etree.XMLParser(encoding='utf-8',remove_blank_text=True)
        string = str(etree.tostring(root, pretty_print=True, encoding='unicode'))
        string = string.encode('utf-8')
        root = etree.XML(string, parser)
        output = b"<?xml version=\"1.0\" encoding=\"utf-8\"?>" + b"\n" + etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=False)
        file.write(output)

def strip_xpath_index(xpath: str):
    """
    Args:
        xpath: Xpath string.

    Returns:
        /A/B[1]/C[2] --> /A/B/C
    """
    return re.sub("\[\d+\]", "", xpath)


def get_all_class_types(cls: Type) -> List[Type]:
    """Get all nested class type from class given.

    Args:
        cls: class type object.

    Returns:
        List of nested class.
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

def read_xml_without_namespace(xml_file: str) -> etree._Element:
    '''This function receive a xml file and return an etree of this xml without any namespace related symbols.

    Eg: 
        {http://www.omg.org/XMI}version -> version
        conf:Conf -> Conf

    Raises:
        Exception: Bug
    '''
    # remove annotation in the origin xml #
    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(xml_file, parser)
    root = tree.getroot()

    # check if the element in the xml has namespace#
    for elem in root.getiterator():
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
            for attribute in elem.attrib:
                j = attribute.find('}')
                if j >= 0:
                    value = elem.attrib[attribute]
                    del elem.attrib[attribute]
                    elem.attrib[attribute[j+1:]] = value
    objectify.deannotate(root, cleanup_namespaces=True)

    if not etree.iselement(root):
        raise Exception("error")

    return tree
