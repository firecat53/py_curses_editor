# -*- coding: utf-8 -*-
import curses
import unittest
import editor.editor as e

str1 = ("Yugoslavia (Latin), Djordje Balasevic, Jugoslavija, "
        "Đorđe Balašević")
str2 = ("ALP, B34130005, Ladies' 7 oz. ComfortSoft® Cotton "
        "Piqué Polo - WHITE - L, "
        "100% ComfortSoft&#174; cotton; Welt-knit collar; "
        "Tag-free neck label; High-stitch density for superior "
        "embellishment platform; "
        "Ash is 99% cotton, 1% polyester; Light Steel is "
        "90% cotton, 10% polyester; Hemmed sleeves; "
        "Sideseamed for a feminine fit; "
        "Narrow, feminine, clean-finished placket with four "
        "dyed-to-match buttons; "
        "8.96, 7.51, 5.78, 035, L 28, 5, WHITE, FFFFFF, 00, .58, "
        "http://www.alphabroder.com/images/alp/prodDetail/035_00_p.jpg, "
        "/images/alp/prodGallery/035_00_g.jpg, 17.92, 035, "
        "00766369145683, 100, no, Hanes, 6, "
        "36, 1007, no, /images/alp/prodDetail/035_00_p.jpg, "
        "/images/alp/backDetail/035_bk_00_p.jpg, "
        "/images/alp/sideDetail/035_sd_00_p.jpg")


class TestIntegration(unittest.TestCase):
    """Integration tests for py_curses_editor. Run through the curses routines
    and some of the non-interactive movements.

    """
    def setUp(self):
        pass

    def main(self, stdscr, *args, **kwargs):
        v = e.Editor(stdscr, *args, **kwargs)
        v.display()
        for key in v.keys:
            if key not in (curses.KEY_F1, curses.ascii.ESC, curses.ascii.ETX):
                v.keys[key]()
        v.keys[curses.KEY_F2]

    def test_1(self):
        curses.wrapper(self.main, title="Test", inittext=str1,
                       win_location=(0, 0), win_size=(50, 80),
                       box=False)

    def test_2(self):
        curses.wrapper(self.main, title=str1, inittext=str2,
                       win_location=(0, 0), win_size=(100, 400),
                       box=True)

    def test_3(self):
        curses.wrapper(self.main, title=str1, inittext=str2,
                       edit=False)


if __name__ == '__main__':
    unittest.main()
