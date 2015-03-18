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
        #self._screen.clear()
        for v in self.views:
            v.draw()
        curses.doupdate()

    def input(self):
        v = None
        for v in reversed(self.views):
            r = v.input()
            if r is None:
                break
        else:
            c = self._screen.getch()
            if c == ord('q') or c == 27 and v is None:
                return False
            elif c == 27:
                self.views[-1].close()
            elif c == curses.KEY_RESIZE:
                self._screen.clear()

        return True

    def cleanup(self):
        new_views = [ v for v in self.views if not v._closed ]
        if len(new_views) != len(self.views):
            self._screen.clear()
        self.views = new_views

    def interact(self):
        while True:
            if len(self.views) == 0:
                return

            # update the memory map
            self._maps = self._mem.maps

            if not self.input():
                return
            self.cleanup()
            time.sleep(0.1)
            self.draw()

from .memview import MemViewAddr
