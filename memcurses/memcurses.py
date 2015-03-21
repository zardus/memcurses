#!/usr/bin/env python

import curses
import logging
l = logging.getLogger('memcurses.memcurses')
l.setLevel('DEBUG')

from .mem import Mem

class MemCurses(object):
    def __init__(self, screen, pid=None, start_addr=None):
        self._mem = Mem(pid=pid)
        self._screen = screen
        self._start_addr = start_addr
        self._x, self._y = (0, 0)

        self._maps = None

        self.views = [ MemViewHex(self._screen.subwin(self.height, self.width, 0, 0), self, start_addr) ]

        self._screen.nodelay(True)
        self._screen.keypad(True)

    @property
    def height(self):
        return self._screen.getmaxyx()[0]

    @property
    def width(self):
        return self._screen.getmaxyx()[1]

    def draw(self):
        #self._screen.clear()
        for v in self.views:
            v.draw()
        curses.doupdate()

    def input(self):
        v = None

        l.debug("memcurses input")
        c = self._screen.getch()
        if c == ord('q'):
            l.debug("... quitting")
            return False
        elif c == ord('x'):
            l.debug("... closing %r", self.views[-1])
            self.views[-1].close()
            self._screen.clear()
        elif c == curses.KEY_RESIZE:
            l.debug("... window resized")
            self._screen.clear()
        else:
            l.debug("... ungetting %r", c)
            curses.ungetch(c)

        for v in reversed(self.views):
            l.debug("Input to %r", v)
            r = v.input()
            if r is None:
                l.debug("... it handled it")
                break
            elif isinstance(r, MemView):
                l.debug("... it created %r", r)
                self.views.append(r)
                self._screen.clear()
                break
        else:
            c = self._screen.getch()
            l.debug("Discarding key %r", c)

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
            self.draw()

from .memview import MemView
from .views import MemViewHex
