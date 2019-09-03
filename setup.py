from setuptools import setup, find_packages

with open("README.md", "r") as file:
    long_description = file.read()


REQUIREMENTS = ["lxml", "loguru"]

CLASSIFIERS = [ 
    'Development Status :: 1 - Planning', 
    'Intended Audience :: Developers', 
    'Topic :: Utilities', 
    'License :: OSI Approved :: MIT License', 
    'Programming Language :: Python', 
    'Programming Language :: Python :: 3.6', 
    'Programming Language :: Python :: 3.7'
] 

# calling the setup function  
setup(name='xml-ormz', 
      version='0.0.4', 
      description='xml-ormz database library mapping collections of xml into python model objects', 
      long_description=long_description, 
      long_description_content_type="text/markdown",
      url='https://github.com/CallmeNezha/xml-ormz', 
      author='ZIJIAN JIANG', 
      author_email='jiangzijian77@gmail.com', 
      license='MIT', 
      packages=find_packages(), 
      include_package_data=True,
      entry_points = {
        'console_scripts': ['xml-ormz=xo.template.generate:main'],
      },
      classifiers=CLASSIFIERS, 
      install_requires=REQUIREMENTS, 
      keywords='xml orm database'
    ) 