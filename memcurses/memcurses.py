#!/usr/bin/env python

import curses
from .mem import Mem

class MemCurses(object):
    def __init__(self, pid=None, start_addr=None, word_size=4):
        self._mem = Mem(pid=pid)
        self._screen = curses.initscr()
        self._start_addr = start_addr
        self._word_size = word_size

    def _display_mem(self, addr):
        self._screen.clear()
        self._screen.border(0)
        height, width = self._screen.getmaxyx()

        # 2 bytes on each side
        # 13 bytes per word
        # -1 since we don't pad the last one
        width_used = 4
        row_words = 0
        while width_used < width:
            if width - width_used >= 3*self._word_size: row_words += 1
            width_used += 3*self._word_size + 1
        max_rows = height - 2

        data = self._mem.read(addr, max_rows * row_words * self._word_size)

        print row_words, max_rows

        i = 0
        for y in range(max_rows):
            cur_x = 2
            for _ in range(row_words):
                for w in range(self._word_size):
                    #print actual_y, actual_x, i
                    self._screen.addstr(y+1, cur_x+w*3, data[i].encode('hex'))
                    i += 1
                cur_x += 3*self._word_size + 1

        self._screen.refresh()

    def interact(self):
        while True:
            self._display_mem(self._start_addr)
            self._screen.getch()
