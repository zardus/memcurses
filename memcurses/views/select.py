import curses

import logging
l = logging.getLogger('memcurses.views.select')
#l.setLevel(logging.DEBUG)

from .message import MemViewMessage

class MemViewSelect(MemViewMessage):
	def __init__(self, memcurses, subject, lines, callback, window=None):
		MemViewMessage.__init__(self, memcurses, subject, lines, window=window)
		self._selected = 0
		self._callback = callback

	def _draw_line(self, y, line, centered=None):
		if line in self._lines and self._lines.index(line) == self._selected:
			self._window.attron(curses.color_pair(2))
			MemViewMessage._draw_line(self, y, line, centered=centered)
			self._window.attroff(curses.color_pair(2))
		else:
			MemViewMessage._draw_line(self, y, line, centered=centered)

	def input(self):
		c = self._window.getch()

		if c == curses.KEY_DOWN:
			self._selected = min(len(self._lines) - 1, self._selected + 1)
		elif c == curses.KEY_UP:
			self._selected = max(0, self._selected - 1)
		elif c == ord('\n'):
			self._callback(self, self._lines[self._selected], self._selected)
