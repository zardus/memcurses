#!/usr/bin/env python

import time
import curses

from .mem import Mem

class MemCurses(object):
    def __init__(self, screen, pid=None, start_addr=None):
        self._mem = Mem(pid=pid)
        self._screen = screen
        self._start_addr = start_addr
        self._height, self._width = self._screen.getmaxyx()
        self._x, self._y = (0, 0)

        self._maps = None

        self.views = [ MemViewAddr(self._screen.subwin(self._height, self._width, 0, 0), self, start_addr) ]

    def draw(self):
        # update the memory map
        self._maps = self._mem.maps

        for v in self.views:
            v.draw()
        curses.doupdate()

    def input(self):
        for v in reversed(self.views):
            r = None
            try:
                if r is not None:
                    curses.ungetch(r)

                r = v.input()
                if r is None:
                    break
                else:
                    continue
            except curses.error:
                raise

    def interact(self):
        while True:
            self.input()
            time.sleep(0.1)
            self.draw()

from .memview import MemViewAddr
