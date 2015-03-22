import curses

import logging
l = logging.getLogger('memcurses.views.debug')
#l.setLevel(logging.DEBUG)

from ..memview import MemView

class MemViewDebug(MemView):
	def __init__(self, memcurses, window=None):
		MemView.__init__(self, memcurses, window=window)

	def draw(self):
		self._window.erase()
		self._window.border(0)

		for i in range(256):
			self._window.addstr(i/6+1, i%6+1, "A", curses.color_pair(i))

		self._window.noutrefresh()

	def input(self):
		c = self._window.getch()
		l.debug("%r ignoring key %r", self, c)
		return None
