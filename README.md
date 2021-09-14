# xml-ormz

**Authors:** ZIJIAN JIANG

**26 Oct 2019**: Alpha version.



xml-ormz is a orm(Object-relational mapping) library for mapping a collection of relational xml files into native python object. It is able to parse xml document tree into hierarchical class `model` objects. When parsing xml document tree into objects, it will check the attributes' `field` type; value content; amount of elements; numbers; `regular expressions`; etc. These validation rules can all be defined by user intuitively. As another important feature, `object relationships` can be built by using `finders`  in xml-ormz, `finder` is a user customized callable object for recursively traverse the trees to build references between any of two or more objects. So in the end of it, you will get a validated mapped relational python objects model *(with no concern about invalid attribute type or values; missing attributes; wrong amount of elements; missing relationships; invalid schema...)*.  In my philosophy of data processing (xml format is one kind of highly complex hierarchical data), all input data should be validated before any following processes, must not let the malignant propagate, and xml-orm do that properly.

API Reference: [https://callmenezha.github.io/xml-ormz/](https://callmenezha.github.io/xml-ormz/)

> Readme is out of date now, please wait.

# 1. Installation

`pip install xml-ormz` 


# 2. Example

It always said one example is beyond any documentation, so let's take a look.

Here is the project hierarchy:

```python
+ ProjectFolder/
	contacts.xml
	addresses.xml
	model.py
	finder.py
	hello.py    # main entry
```

Let's say we have two xml files.

```xml
<!-- contacts.xml -->
<Contacts>
    <Person name="Alice" address="Wonderland Street No.231">
        <Email>513754619@mail.com</Email>
    	<Phone number="513754619"/>
        <Phone number="611953242"/>
    </Person> 
    <Person name="Rabbit" address="Moon Street No.1">
        <Email>645118456@gmail.com</Email>
    	<Phone number="645118456"/>
    </Person> 
</Contacts>
```

```xml
<!-- addresses.xml -->
<Addresses>
	<Apartment location="Wonderland Street No.231" year="1898" owner="Queen of Hearts"/>
    <Apartment location="Moon Street No.1" year="2" area="401"/>
</Addresses>
```



1. We create `model.py` for class model definitions.

```python
# model.py

from xo.orm import Model, Optional, StringField, FloatField, IntegerField, ForeignKeyField

class Contacts(Model):

    class Person(Model):
        name    = StringField(re=r"(Alice|Rabbit|John)")  # regular expression validation
        address = StringField()

        class Email(Model):
            __count__ = 1   # every person must have one and only one email
            pass			# email address is in email.text and text is not a attribute
        
        class Phone(Model):
            __count__ = (1, ) # every person must have at least one phone
            number = IntegerField( primary_key=True )


class Addresses(Model):
    
    class Apartment(Model):
        location = StringField( primary_key=True )
        year = IntegerField()
        owner = Optional( StringField() ) # owner attribute can be none, not required (without it will raise an error)
		# forget to define `area` field here 
        # when you run the program it will warn you that:
        # 2019-08-29 15:21:40 X root[7828] WARNING Try to assign extra attribute 'area' to undefined field of 'Addresses.Apartment', drop it.
        # So your `area` attribute in addresses.xml will never appear in this object.
```

   

3. Create main entry of program `hello.py`

```python
# hello.py

from model import Contacts, Addresses
from xo.crawler import XmlMapper

address_map = XmlMapper("./addresses.xml", Addresses).parse()
contact_map = XmlMapper("./contacts.xml", Contacts).parse()
```



```python
Result:
address_map - 
  +  '/Addresses':<class Addresses>
      -  'childApartment':[<class Addresses.Apartment>]
      -  'childHouse':[<class Addresses.House>]
      -  'text':''
  +  '/Addresses/Apartment[1]':<class Addresses.Apartment>
      -  'location':'Wonderland Street No.231'
      -  'owner':'Queen of Hearts'
      -  'parentAddresses':<class Addresses>
      -  'year':1898
  +  '/Addresses/Apartment[2]':<class Addresses.Apartment>
      -  'location':'Moon Street No.1'
      -  'parentAddresses':<class Addresses>
      -  'year':2


contact_map - 
  +  '/Contacts': <class Contacts>
  +  '/Contacts/Person[1]': <class Contacts.Person>
  +  '/Contacts/Person[1]/Email': <class Contacts.Person.Email>
      -  'parentPerson':<class Contacts.Person>
      -  'text':'513754619@mail.com'
  +  '/Contacts/Person[1]/Phone[1]': <class Contacts.Person.Phone>
  +  '/Contacts/Person[1]/Phone[2]': <class Contacts.Person.Phone>
  +  '/Contacts/Person[2]': <class Contacts.Person>
  +  '/Contacts/Person[2]/Email': <class Contacts.Person.Email>
  +  '/Contacts/Person[2]/Phone': <class Contacts.Person.Phone>
  ...

```

