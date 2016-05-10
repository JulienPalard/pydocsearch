#!/usr/bin/env python

from distutils.core import setup

setup(name='pydocsearch',
      version='1.0.1',
      description='Search a page in docs.python.org',
      long_description=open('README.rst', 'rt').read(),
      author='Julien Palard',
      author_email='julien@palard.fr',
      keywords=['pydoc', 'docs.python.org', 'search'],
      url='https://github.com/JulienPalard/pydocsearch',
      download_url='https://github.com/julienpalard/pydocsearch/tarball/1.0.1',
      py_modules=['pydocsearch'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License'])
