#!/usr/bin/env python

import os
from distutils.core import setup

def contents_of(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return 'BitWizard Api'


setup(name='BitWizard',
      version='0.2-b',
      description='BitWizard API',
      long_description=contents_of('README.rst'),
      author='Martijn Moeling, Home.Nl',
      author_email='martijn@moeling.net',
      url='',
      
      license="LGPL or MIT",
      
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License (LGPL)'
        'License :: OSI Approved :: MIT',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Topic :: Raspberry Pi BitWizard API',
      ],
      platforms=['Linux'],
      
      provides=['BitWizard'],
      packages=['BitWizard'],
      package_dir = {'': 'src'},
      scripts=[],
      
      requires=['smbus']
)
