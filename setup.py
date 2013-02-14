#!/usr/bin/env python

from distutils.core import setup

setup(
        name = "py_curses_editor",
        version = "1.0",
        description = "A configurable curses text editor window",
        long_description = open('README.rst').read(),
        author = "Scott Hansen",
        author_email = "firecat4153@gmail.com",
        url = "https://github.com/firecat53/py_curses_editor",
        packages = ['editor'],
        package_data = {'editor': ['README.rst']},
        data_files = [('share/doc/py_curses_editor',
                       ['README.rst', 'LICENSE.txt'])],
        license = "MIT",
)
