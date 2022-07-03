#!/usr/bin/env python

from setuptools import setup

setup(name="py_curses_editor",
      version="1.3.0",
      description="A configurable curses text editor window",
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      author="Scott Hansen",
      author_email="firecat4153@gmail.com",
      url="https://github.com/firecat53/py_curses_editor",
      download_url="https://github.com/firecat53/py_curses_editor/tarball/1.3.0",
      packages=['editor'],
      package_data={'editor': ['README.md']},
      data_files=[('share/doc/py_curses_editor',
                   ['README.md', 'LICENSE.txt', 'CHANGELOG.md'])],
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
          'Programming Language :: Python :: 3',
          'Topic :: Text Editors',
          'Topic :: Utilities',
      ],
      keywords='editor console curses utility',
      )
