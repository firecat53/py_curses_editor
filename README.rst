py_curses_editor  
================

Python curses text editor module. Provides a configurable pop-up window for
entering text, passwords, etc.

Posted by Scott Hansen <firecat4153@gmail.com>

Other Contributors:

    + Yuri D'Elia <wavexx@thregr.org> (Unicode/python2 code from tabview)

Features:
---------
* Python 2.7+, 3+
* Unicode support
* Configurable window size and location
* Text box can have a title and/or an outlined box
* Text box can be initialized with existing text to edit
* Password mode for hiding text entries
* Paste in large blocks of text from primary clipboard
* Pop-up help menu

Requires: 
---------

Python 2.7+, 3+

Installation:
-------------

* ``# python setup.py install``  OR
* ``$ python setup.py install --user``

License:
--------

* MIT

Usage:
------

From non-curses application::

    import editor
    editor.editor(box=False, inittext="Hi", win_location=(5, 5))

From curses application with a predefined curses window object (stdscr)::

    from editor.editor import Editor
    Editor(stdscr, win_size=(1,80), pw_mod=True, max_text_size=1)()

Keybindings:
------------

=====================    ====================================================
**F1**                   Show popup help menu
**F2 or Ctrl-x**         Save and Quit
**Enter**                Enter new line, or Save and Quit in single line mode
**F3, Ctrl-c or ESC**    Cancel (no save)
**Cursor keys**          Movement
**Ctrl-n/p Ctrl-f/b**    Up/down right/left
**Home/End Ctrl-a/e**    Beginning or End of current line
**PageUp/PageDown**      PageUp/PageDown
**Delete/Ctrl-d**        Delete character under cursor
**Backspace/Ctrl-h**     Delete character to left
**Ctrl-k/u**             Delete to end/beginning of-line
**Ctrl-v**               Paste a block of text from primary clipboard
                           (requires xclip or xsel)
=====================    ===================================================

Notes:
------

Using shift-insert to paste text will be quite slow, as it's pasting one
character at a time. Use Ctrl-v to paste a large block of text from the primary
clipboard.

Double-width characters are not yet supported.
