from setuptools import setup, find_packages

with open("README.md", "r") as file:
    long_description = file.read()


REQUIREMENTS = ["lxml"]

CLASSIFIERS = [ 
    'Development Status :: 1 - Beta', 
    'Intended Audience :: Developers', 
    'Topic :: XML ORM', 
    'License :: OSI Approved :: MIT License', 
    'Programming Language :: Python', 
    'Programming Language :: Python :: 3.6', 
    'Programming Language :: Python :: 3.7'
] 

# calling the setup function  
setup(name='xml-orm', 
      version='0.0.1', 
      description='xml-orm database library mapping collections of xml into python model objects', 
      long_description=long_description, 
      url='', 
      author='ZIJIAN JIANG', 
      author_email='jiangzijian77@gmail.com', 
      license='MIT', 
      packages=find_packages(), 
      classifiers=CLASSIFIERS, 
      install_requires=REQUIREMENTS, 
      keywords='xml orm database'
    ) 