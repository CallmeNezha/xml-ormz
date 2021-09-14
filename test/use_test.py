from xo.orm.mapper import XmlMapper
from xo.orm import Model, StringField, IntegerField, Optional, ForeignKeyField

import os
import unittest


# Model for contacts.xml
class Contacts(Model):
    
    class Person(Model):
        address = StringField()
        name = StringField()
        
        class Email(Model):
            pass

        class Phone(Model):
            number = IntegerField()
            
        
# Model for addresses.xml
class Addresses(Model):
    
    class Apartment(Model):
        area = Optional( IntegerField() )
        location = StringField()
        owner = Optional( StringField() )
        year = IntegerField()


contacts_xmlfile = os.path.join(os.path.dirname(__file__), "contacts.xml")
addresses_xmlfile = os.path.join(os.path.dirname(__file__), "addresses.xml")



#print(orm_map['/Contacts'].getChildren('Email', recursive=True))

class XmlMapperTestCase(unittest.TestCase):
    def setUp(self):
        self.contacts_mapper = XmlMapper(contacts_xmlfile, Contacts)
        self.addresses_mapper = XmlMapper(addresses_xmlfile, Addresses)

    def test_xmlmapper(self):
        contacts = self.contacts_mapper.parse()
        addresses = self.addresses_mapper.parse()

    def test_model_getchildren(self):
        contacts = self.contacts_mapper.parse()
        self.assertEqual(len(contacts['/Contacts'].getChildren()), 2)
        self.assertEqual(len(contacts['/Contacts'].getChildren("Person")), 2)
        self.assertEqual(len(contacts['/Contacts'].getChildren("Email")), 0)
        self.assertEqual(len(contacts['/Contacts'].getChildren("Email", recursive=True)), 2)
        self.assertEqual(len(contacts['/Contacts'].getChildren("Phone", recursive=True)), 3)
        
    def test_model_getparent(self):
        contacts = self.contacts_mapper.parse()
        self.assertEqual(contacts['/Contacts'].getChildren()[0].getParent(), contacts['/Contacts'])

    # TODO: add more test cases.