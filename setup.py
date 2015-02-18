#!/usr/bin/env python

from distutils.core import setup
import setuptools

setup(name="py_curses_editor",
      version="1.2.1",
      description="A configurable curses text editor window",
      long_description=open('README.rst').read(),
      author="Scott Hansen",
      author_email="firecat4153@gmail.com",
      url="https://github.com/firecat53/py_curses_editor",
      download_url="https://github.com/firecat53/py_curses_editor/tarball/1.2.1",
      packages=['editor'],
      package_data={'editor': ['README.rst']},
      data_files=[('share/doc/py_curses_editor',
                   ['README.rst', 'LICENSE.txt', 'CHANGELOG.rst'])],
      license="MIT",
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Environment :: Console :: Curses',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Text Editors',
          'Topic :: Utilities',
      ],
      keywords='editor console curses utility',
      )
