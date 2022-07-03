"""Py_curses_editor

Copyright (c) 2022, Scott Hansen <firecat4153@gmail.com>

"""
import curses
import curses.ascii
import locale
import os
import string
import sys
from collections import namedtuple
from subprocess import Popen, PIPE
from textwrap import wrap
import _curses


def CTRL(key):
    """ Args: key

    """
    return curses.ascii.ctrl(key)


def addstr(*args):
    """ Wrapper """
    scr, args = args[0], args[1:]
    return scr.addstr(*args)


class Editor(object):
    """ Basic python curses text editor class.

    Can be used for multi-line editing.

    Text will be wrapped to the width of the editing window, so there will be
    no scrolling in the horizontal direction. For now, there's no line
    wrapping, so lines will have to be wrapped manually.

    Args:
        stdscr:         the curses window object
        title:          title text
        inittext:       inital text content string
        win_location:   tuple (y,x) for location of upper left corner
        win_size:       tuple (rows,cols) size of the editor window
        box:            True/False whether to outline editor with a box
        max_paragraphs: maximum paragraphs (text separated by \n) allowed.
                            Default=0 (unlimited)
                            If initext is longer than max_paragraphs, extra
                            lines _will be truncated_!
        pw_mode:        True/False. Whether or not to show text entry
                            (e.g. for passwords)
        edit:           True/False. Default is True for editor. Use False
                            to have a scrollable popup window.

    Returns:
        text:   text string

    Usage: (from non-curses application)
        import editor
        editor.editor(box=False, inittext="Hi", win_location=(5, 5))

    Usage: (from curses application with a defined curses window object)
        from editor.editor import Editor
        Editor(stdscr, win_size=(1,80), pw_mod=True, max_paragraphs=1)()

    """

    def __init__(self, scr, title="", inittext="", win_location=(0, 0),
                 win_size=(20, 80), box=True, max_paragraphs=0, pw_mode=False,
                 edit=True):
        # Fix for python curses resize bug:
        # http://bugs.python.org/issue2675
        os.unsetenv('LINES')
        os.unsetenv('COLUMNS')
        self.scr = scr
        self.title_orig = title
        self.box = box
        self.max_paragraphs = max_paragraphs
        self.pw_mode = pw_mode
        self.edit = edit
        self.win_location_orig_y, self.win_location_orig_x = win_location
        self.win_size_orig_y, self.win_size_orig_x = win_size
        self.win_size_y = self.win_size_orig_y
        self.win_size_x = self.win_size_orig_x
        self.win_location_y = self.win_location_orig_y
        self.win_location_x = self.win_location_orig_x
        self.win_init()
        self.box_init()
        self.text_init(inittext)
        if self.edit is False:
            self.keys_init_noedit()
            try:
                curses.curs_set(0)
            except _curses.error:
                pass
        else:
            self.keys_init()
            curses.curs_set(1)
        self.display()

    def __call__(self):
        self.run()
        curses.flushinp()
        return "\n".join(["".join(i) for i in self.text])

    def win_init(self):
        """Set initial editor window size parameters, and reset them if window
        is resized.

        """
        # self.cur_pos is the current y,x position of the cursor relative to
        # the visible area of the box
        self.cur_pos_y = 0
        self.cur_pos_x = 0
        # y_offset controls the up-down scrolling feature
        self.y_offset = 0
        # Position of the cursor relative to the upper left corner of the data
        # (self.flattend_text)
        self.buffer_idx_y = 0
        self.buffer_idx_x = 0
        # Make sure requested window size is < available window size
        self.max_win_size_y, self.max_win_size_x = self.scr.getmaxyx()
        # Keep the input box inside the physical window
        self.win_size_y = min(self.win_size_orig_y, self.max_win_size_y)
        self.win_size_x = min(self.win_size_orig_x, self.max_win_size_x)
        # Validate win_location settings
        self.win_location_x = min(max(0, self.max_win_size_x -
                                      self.win_size_x),
                                  self.win_location_orig_x)
        self.win_location_y = min(max(0, self.max_win_size_y -
                                      self.win_size_y),
                                  self.win_location_orig_y)
        # Adjust max_win_size for different possible offsets
        # (e.g. if there is a title and/or a box) and initiate the curses
        # screen(s)
        self._win_scr_init()
        self.title, self.title_help = self._title_init()
        self.stdscr.keypad(1)
        try:
            curses.use_default_colors()
        except _curses.error:
            pass
        if self.pw_mode is True:
            try:
                curses.curs_set(0)
            except _curses.error:
                pass

    def _win_scr_init(self):
        """Initialize the curses window objects  (called from win_init)

            self.stdscr - the text display area
            self.boxscr - for the box outline and title, if applicable

        """
        # Create an extra window for the box outline and/or title, if required
        self.x_off = self.y_off = loc_off_y = loc_off_x = 0
        if self.box:
            # Compensate for the box lines
            self.y_off += 2
            self.x_off += 2
            # The text box location is offset because of the box
            loc_off_y += 1
            loc_off_x += 1
        if self.title_orig:
            self.y_off += 1
            loc_off_y += 1
        if self.box is True or self.title_orig:
            # Make box/title screen bigger than actual text area (stdscr)
            self.boxscr = self.scr.subwin(self.win_size_y,
                                          self.win_size_x,
                                          self.win_location_y,
                                          self.win_location_x)
            self.win_size_y = max(1, self.win_size_y - self.y_off)
            self.win_size_x = max(1, self.win_size_x - self.x_off)
            self.stdscr = self.scr.subwin(self.win_size_y,
                                          self.win_size_x,
                                          self.win_location_y + loc_off_y,
                                          self.win_location_x + loc_off_x)
        else:
            self.stdscr = self.scr.subwin(self.win_size_y,
                                          self.win_size_x,
                                          self.win_location_y,
                                          self.win_location_x)

    def text_init(self, text):
        """Transform text string into a list of list of strings, wrapped to
        fit the window size. Sets the dimensions of the text buffer. Each
        paragraph is a new list.

        self.text = [['This is a', 'long paragraph'], ['short one']]
                            ^this list^ is wrapped together as a paragraph

        """
        self.text = [self._text_wrap(i) or [""]
                     for i in text.splitlines() or [""]]
        self.text_orig = list(self.text)
        if self.max_paragraphs:
            # Truncates initial text if max_paragraphs < len(self.text)
            self.text = self.text[:self.max_paragraphs]

    def box_init(self):
        """Clear the main screen and redraw the box and/or title

        """
        # Touchwin seems to save the underlying screen and refreshes it (for
        # example when the help popup is drawn and cleared again)
        self.scr.touchwin()
        self.scr.refresh()
        self.stdscr.clear()
        self.stdscr.refresh()
        if self.box is True:
            self.boxscr.clear()
            self.boxscr.box()
            if self.title:
                addstr(self.boxscr, 1, 1, self.title, curses.A_BOLD)
                addstr(self.boxscr, self.title_help, curses.A_STANDOUT)
            self.boxscr.refresh()
        elif self.title:
            self.boxscr.clear()
            addstr(self.boxscr, 0, 0, self.title, curses.A_BOLD)
            addstr(self.boxscr, self.title_help, curses.A_STANDOUT)
            self.boxscr.refresh()

    def keys_init(self):
        """Define methods for each key.

        """
        self.keys = {
            curses.KEY_BACKSPACE:           self.backspace,
            CTRL('h'):                      self.backspace,
            curses.ascii.BS:                self.backspace,
            curses.ascii.DEL:               self.backspace,
            curses.ascii.ETX:               self.close,
            curses.KEY_DC:                  self.del_char,
            CTRL('d'):                      self.del_char,
            CTRL('u'):                      self.del_to_bol,
            CTRL('k'):                      self.del_to_eol,
            curses.KEY_DOWN:                self.down,
            CTRL('n'):                      self.down,
            curses.KEY_END:                 self.end,
            CTRL('e'):                      self.end,
            curses.KEY_F1:                  self.help,
            curses.KEY_HOME:                self.home,
            CTRL('a'):                      self.home,
            curses.KEY_ENTER:               self.insert_line_or_quit,
            curses.ascii.NL:                self.insert_line_or_quit,
            curses.ascii.LF:                self.insert_line_or_quit,
            "\n":                           self.insert_line_or_quit,
            curses.KEY_LEFT:                self.left,
            CTRL('b'):                      self.left,
            curses.KEY_NPAGE:               self.page_down,
            curses.KEY_PPAGE:               self.page_up,
            CTRL('v'):                      self.paste,
            CTRL('x'):                      self.quit,
            curses.KEY_F2:                  self.quit,
            curses.KEY_F3:                  self.quit_nosave,
            curses.ascii.ESC:               self.quit_nosave,
            curses.KEY_RESIZE:              self.resize,
            -1:                             self.resize,
            curses.KEY_RIGHT:               self.right,
            CTRL('f'):                      self.right,
            curses.KEY_UP:                  self.up,
            CTRL('p'):                      self.up,
        }

    def keys_init_noedit(self):
        """Define methods for each key for non-editing mode.

        """
        self.keys = {
            curses.ascii.ETX:               self.close,
            curses.KEY_DOWN:                self.down_noedit,
            CTRL('n'):                      self.down_noedit,
            'j':                            self.down_noedit,
            curses.KEY_F1:                  self.help,
            curses.KEY_NPAGE:               self.page_down,
            'J':                            self.page_down,
            CTRL('f'):                      self.page_up,
            curses.KEY_PPAGE:               self.page_up,
            'K':                            self.page_up,
            CTRL('b'):                      self.page_up,
            CTRL('x'):                      self.quit,
            'q':                            self.quit,
            curses.KEY_F2:                  self.quit,
            curses.KEY_F3:                  self.quit_nosave,
            curses.ascii.ESC:               self.quit_nosave,
            curses.KEY_RESIZE:              self.resize,
            -1:                             self.resize,
            curses.KEY_UP:                  self.up_noedit,
            CTRL('p'):                      self.up_noedit,
            'k':                            self.up_noedit,
        }

    def _title_init(self):
        """Initialze box title and help string

        """
        self.title = self.title_orig[:self.win_size_x]
        if len(self.title) >= self.win_size_x:
            self.title = self.title[:-3] + ".."
        if self.max_paragraphs == 1 and self.edit is True:
            quick_help = "   F2/Enter/^x: Save, F3/ESC/^c: Cancel"
        elif self.edit is False:
            quick_help = "   q/F2/^c: Quit, j/k: Scroll up/down"
        else:
            quick_help = "   F2/^x: Save, F3/ESC/^c: Cancel"
        if len(self.title) + len(quick_help) > self.win_size_x - 2:
            return self.title, quick_help[:self.win_size_x -
                                          len(self.title) - 3] + ".."
        else:
            return self.title, quick_help

    def _text_wrap(self, text):
        """Given text as a list of text strings, where the list is
        a paragraph, run wordwrap on the paragraph.

        Args: text - ["str1 asdf", "str2",...]
        Returns: text ["str1 asdf", "str2",...]

        """
        # Use win_size_x - 1 so addstr has one more cell at the end to put the
        # cursor
        return wrap("".join(text), self.win_size_x - 1,
                    drop_whitespace=False) or [""]

    def left(self):
        if self.cur_pos_x > 0:
            self.cur_pos_x = self.cur_pos_x - 1
        elif self.cur_pos_x == 0 and self.buffer_idx_y > 0:
            self.up()
            self.end()
        self._set_buffer_idx_x()

    def right(self):
        if self.cur_pos_x < self.win_size_x and \
                self.cur_pos_x < self.buf_line_length:
            self.cur_pos_x = self.cur_pos_x + 1
        elif self.buffer_idx_y == len(self.flattened_text) - 1:
            pass
        else:
            self.down()
            self.home()
        self._set_buffer_idx_x()

    def up(self):
        if self.cur_pos_y > 0:
            self.cur_pos_y = self.cur_pos_y - 1
        else:
            self.y_offset = max(0, self.y_offset - 1)
        self._set_buffer_idx_y()
        self._set_buffer_idx_x()

    def up_noedit(self):
        self.y_offset = max(0, self.y_offset - 1)

    def down(self):
        if self.cur_pos_y < self.win_size_y - 1 and \
                self.buffer_idx_y < len(self.flattened_text) - 1:
            self.cur_pos_y = self.cur_pos_y + 1
        elif self.buffer_idx_y == len(self.flattened_text) - 1:
            pass
        else:
            self.y_offset = min(self.buffer_rows - self.win_size_y,
                                self.y_offset + 1)
        self._set_buffer_idx_y()
        self._set_buffer_idx_x()

    def down_noedit(self):
        self.y_offset = min(self.buffer_rows - self.win_size_y,
                            self.y_offset + 1)

    def end(self):
        self.cur_pos_x = self.buf_line_length
        self._set_buffer_idx_x()

    def home(self):
        self.cur_pos_x = 0
        self._set_buffer_idx_x()

    def page_up(self):
        if self.cur_pos_y > 0 and self.y_offset == 0:
            self.cur_pos_y = 0
        self.y_offset = max(0, self.y_offset - self.win_size_y)
        self._set_buffer_idx_y()
        self._set_buffer_idx_x()

    def page_down(self):
        if len(self.flattened_text) < self.win_size_y and \
                self.y_offset == 0:
            self.cur_pos_y = len(self.flattened_text) - 1
        elif self.cur_pos_y < self.win_size_y and \
                self.y_offset >= self.buffer_rows - self.win_size_y:
            self.cur_pos_y = self.win_size_y - 1
        self.y_offset = min(self.buffer_rows - self.win_size_y,
                            self.y_offset + self.win_size_y)
        # Corrects negative offsets
        self.y_offset = max(0, self.y_offset)
        self._set_buffer_idx_y()
        self._set_buffer_idx_x()

    @property
    def line(self):
        """Return current line (paragraph) as a string

        """
        return "".join(self.text[self.paragraph.para_index])

    @line.setter
    def line(self, value):
        """Set current displayed paragraph and word wrap it.

        Args: value - string

        """
        p_idx, l_idx, _ = self.paragraph
        self.text[p_idx] = self._text_wrap([value])

    @property
    def flattened_text(self):
        """Return a flattened self.text (single list of strings)

        """
        return [j for i in self.text for j in i] or [""]

    def _char_index_to_yx(self, para_index, char_index):
        """Given the char_index for a paragraph, set buffer_idx_y,
        buffer_idx_x, cur_pos_y and cur_pos_x

        """
        line_idx = c_index = 0
        done = False
        for line_idx, line in enumerate(self.text[para_index]):
            x_pos = 0
            for c in line:
                if c_index == char_index:
                    done = True
                    break
                c_index += 1
                x_pos += 1
            if done is True:
                break
        self.buffer_idx_x = x_pos
        prev_paras_len = sum(map(len, self.text[:para_index]))
        self.buffer_idx_y = prev_paras_len + line_idx
        while self.buffer_idx_y - self.y_offset >= self.win_size_y:
            self.y_offset += 1
        while self.buffer_idx_y - self.y_offset < 0:
            self.y_offset -= 1
        self.cur_pos_y = self.buffer_idx_y - self.y_offset
        self.cur_pos_x = self.buffer_idx_x

    @property
    def paragraph(self):
        """Return the index within self.text of the current paragraph and of
        the current line and current character (number of characters since the
        start of the paragraph) within the paragraph

        Returns: namedtuple (para_index, line_index, char_index)

        """
        idx_para = idx_buffer = idx_line = idx_char = 0
        done = False
        for para in self.text:
            for idx_line, line in enumerate(para):
                if idx_buffer == self.buffer_idx_y:
                    done = True
                    break
                idx_buffer += 1
            if done is True:
                break
            idx_para += 1
        idx_char = sum(map(len, self.text[idx_para][:idx_line])) + \
            self.buffer_idx_x
        p = namedtuple("para", ['para_index', 'line_index', 'char_index'])
        return p(idx_para, idx_line, idx_char)

    @property
    def line_length(self):
        """Return the string length of the current complete line (paragraph)

        """
        return len(self.line)

    @property
    def buf_line(self):
        """Return a string for the current display buffer row

        """
        return self.flattened_text[self.buffer_idx_y]

    @property
    def buf_line_length(self):
        """Return the string length of the current single displayed row

        """
        return len(self.buf_line)

    @property
    def buffer_rows(self):
        """Return length of text buffer or visible window length, whichever is
        greater.

        """
        return max(self.win_size_y, len(self.flattened_text))

    def _set_buffer_idx_y(self):
        """Set buffer_idx_y (y position in self.flattened_text)

        """
        if self.cur_pos_y + self.y_offset > len(self.flattened_text) - 1:
            self.buffer_idx_y = len(self.flattened_text)
        else:
            self.buffer_idx_y = self.cur_pos_y + self.y_offset

    def _set_buffer_idx_x(self):
        """Set buffer_idx_x (x position in self.flattened_text

        This doesn't matter much right now because it will always be the same
        as self.cur_pos_x because we don't have side-scrolling yet.

        """
        if self.cur_pos_x > self.buf_line_length:
            self.cur_pos_x = self.buf_line_length
        self.buffer_idx_x = self.cur_pos_x

    def insert_char(self, c):
        """Given an integer character, insert that character in the current
        line. Stop when the maximum line length is reached.

        """
        if c not in string.printable:
            return
        para_idx, line_idx, char_idx = self.paragraph
        line = list(self.line)
        line.insert(char_idx, c)
        char_idx += 1
        self.line = "".join(line)
        self._char_index_to_yx(para_idx, char_idx)

    def insert_line_or_quit(self):
        """Insert a new line at the cursor. Wrap text from the cursor to the
        end of the line to the next line. If the line is a single line, saves
        and exits.

        """
        if self.max_paragraphs == 1:
            # Save and quit for single-line entries
            return False
        if 0 < self.max_paragraphs <= len(self.text):
            return
        p_idx, _, c_idx = self.paragraph
        newline = self.line[c_idx:]
        line = self.line[:c_idx]
        self.text[p_idx] = self._text_wrap([line])
        self.text.insert(p_idx + 1, self._text_wrap([newline]))
        self._char_index_to_yx(p_idx + 1, 0)

    def backspace(self):
        """Delete character to the left of the cursor and move one space left.

        """
        para_idx, line_idx, char_idx = self.paragraph
        line = list(self.line)
        if char_idx > 0:
            del line[char_idx - 1]
            char_idx -= 1
            self.line = "".join(line)
        elif para_idx > 0 and char_idx == 0:
            oldline = "".join(self.text[para_idx - 1])
            newline = oldline + "".join(line)
            self.text[para_idx - 1] = self._text_wrap([newline])
            del self.text[para_idx]
            char_idx = len(oldline)
            para_idx -= 1
        else:
            pass
        self._char_index_to_yx(para_idx, char_idx)

    def del_char(self):
        """Delete character under the cursor.

        """
        para_idx, line_idx, char_idx = self.paragraph
        line = list(self.line)
        if line and char_idx < len(line):
            del line[char_idx]
            self.line = "".join(line)
        elif char_idx == len(line) and para_idx < len(self.text) - 1:
            nextline = "".join(self.text[para_idx + 1])
            self.line = "".join("".join(line) + nextline)
            del self.text[para_idx + 1]
        else:
            pass
        self._char_index_to_yx(para_idx, char_idx)

    def del_to_eol(self):
        """Delete from cursor to end of current line. (C-k)

        """
        para_idx, line_idx, char_idx = self.paragraph
        start = self.line[:char_idx]
        clip_len = self.buf_line_length - self.buffer_idx_x
        end = self.line[char_idx + clip_len:]
        self.line = start + end

    def del_to_bol(self):
        """Delete from cursor to beginning of current line. (C-u)

        """
        para_idx, line_idx, char_idx = self.paragraph
        start = self.line[:char_idx - self.buffer_idx_x]
        end = self.line[char_idx:]
        self.line = start + end
        self._char_index_to_yx(para_idx, char_idx - self.buffer_idx_x)

    def paste(self):
        """Use xsel or xclip if available to paste and process a large chunk of
        text all at once.

        """
        res = ""
        try:
            os.environ['DISPLAY']
        except KeyError:
            return
        for cmd in (['xclip', '-o', '-selection', 'primary'],
                    ['xsel', '-o', '--primary']):
            try:
                res = Popen(cmd, stdout=PIPE,
                            universal_newlines=True).communicate()[0]
            except IOError:
                continue
            else:
                break
        para_idx, line_idx, char_idx = self.paragraph
        if not res:
            return
        if sys.version_info.major < 3:
            enc = locale.getpreferredencoding() or 'utf-8'
            res = str(res, encoding=enc)
        res = res.splitlines()
        if len(res) == 1:
            line = list(self.line)
            cur_line_paste = list(res[0])
            line[char_idx:char_idx] = cur_line_paste
            char_idx += len(cur_line_paste)
            self.line = "".join(line)
        else:
            line = list(self.line)
            beg_line = line[:char_idx]
            end_line = "".join(line[char_idx:])
            first_line_paste = list(res[0])
            beg_line.extend(first_line_paste)
            self.line = "".join(beg_line)
            ins = [self._text_wrap(i) for i in res[1:]]
            self.text[para_idx + 1:para_idx + 1] = ins
            para_idx += len(res[1:])
            self.text[para_idx].append(end_line)
            self.text[para_idx] = self._text_wrap(self.text[para_idx])
            char_idx = sum(len(i) for i in self.text[para_idx])
        self._char_index_to_yx(para_idx, char_idx)

    def quit(self):
        return False

    def quit_nosave(self):
        self.edit = False  # Used to detect that quit_nosave was triggered
        self.text = self.text_orig
        return False

    def help(self):
        """Display help text popup window.

        """
        help_txt = (" Save and exit         : F2 or Ctrl-x\n"
                    "            (Enter if in single-line entry mode)\n"
                    " Exit (no save)        : F3, Ctrl-c or ESC\n"
                    " Cursor movement       : Arrow keys/Ctrl-f/b/n/p\n"
                    " Beginning of line     : Home/Ctrl-a\n"
                    " End of line           : End/Ctrl-e\n"
                    " Page Up/Page Down     : PgUp/PgDn\n"
                    " Backspace/Delete      : Backspace/Ctrl-h\n"
                    " Delete current char   : Del/Ctrl-d\n"
                    " Insert line at cursor : Enter\n"
                    " Paste block of text   : Ctrl-v\n"
                    " Delete to end of line : Ctrl-k\n"
                    " Delete to BOL         : Ctrl-u\n")
        help_txt_no = (" Quit                : q,F2,F3,ESC,Ctrl-c or Ctrl-x\n"
                       " Cursor movement     : Arrow keys/j-k/Ctrl-n/p\n"
                       " Page Up/Page Down   : J/K/PgUp/PgDn/Ctrl-b/n\n")
        if self.edit is False:
            help_txt = help_txt_no
        txt = help_txt.splitlines()
        try:
            curses.curs_set(0)
        except _curses.error:
            pass
        lines = len(txt) + 2
        cols = max([len(i) for i in txt]) + 2
        # Only print help text if the window is big enough
        try:
            popup = curses.newwin(lines, cols, self.win_location_y,
                                  self.win_location_x)
            addstr(popup, 1, 0, "\n".join(txt))
            popup.box()
        except _curses.error:
            pass
        else:
            while not popup.getch():
                pass
        finally:
            # Turn back on the cursor
            if self.pw_mode is False and self.edit is True:
                curses.curs_set(1)
            # flushinp Needed to prevent spurious F1 characters being written
            # to line
            curses.flushinp()
            self.box_init()

    def resize(self):
        """Handle window resizing."""
        if curses.is_term_resized(self.max_win_size_y, self.max_win_size_x):
            self.win_init()
            self.box_init()
            self.text = [self._text_wrap(i) for i in self.text]
            curses.resizeterm(self.max_win_size_y, self.max_win_size_x)

    def run(self):
        """Main program loop.

        """
        try:
            while True:
                self.stdscr.move(self.cur_pos_y, self.cur_pos_x)
                loop = self.get_key()
                if loop is False:
                    break
                self.display()
        except KeyboardInterrupt:
            self.text = self.text_orig
        return "\n".join(["".join(i) for i in self.text])

    def display(self):
        """Display the editor window and the current contents.

        """
        self.stdscr.erase()
        y_idx = display_idx = 0
        done = False
        for para in self.text:
            for line_idx, line in enumerate(para):
                if y_idx >= self.y_offset and display_idx < self.win_size_y:
                    if not self.pw_mode:
                        addstr(self.stdscr, display_idx, 0, line)
                    if len(self.text) > 1 and line_idx == len(para) - 1 \
                            and self.edit is True:
                        # Show an end of paragraph marker on last line.
                        self.stdscr.insch(display_idx, self.win_size_x - 1,
                                          curses.ACS_LARROW)
                    display_idx += 1
                elif display_idx >= self.win_size_y:
                    done = True
                    break
                y_idx += 1
            if done is True:
                break
        self.stdscr.refresh()

    def close(self):
        self.text = self.text_orig
        curses.endwin()
        curses.flushinp()
        return False

    def get_key(self):
        c = self.stdscr.getch()
        if c == curses.KEY_RESIZE:
            self.resize()
            return True
        # 127 and 27 are to make sure the Backspace/ESC keys work properly
        if 0 < c < 256 and c != 127 and c != 27:
            c = chr(c)
        try:
            loop = self.keys[c]()
        except KeyError:
            if self.edit is True:
                self.insert_char(c)
            loop = True
        return loop


def main(stdscr, **kwargs):
    return Editor(stdscr, **kwargs)()


def editor(**kwargs):
    os.environ['ESCDELAY'] = '25'
    return curses.wrapper(main, **kwargs)


editor.__doc__ = Editor.__doc__
