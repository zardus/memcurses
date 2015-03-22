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
			self._window.attron(curses.A_STANDOUT)
			MemViewMessage._draw_line(self, y, line, centered=centered)
			self._window.attroff(curses.A_STANDOUT)
		else:
			MemViewMessage._draw_line(self, y, line, centered=centered)

	@property
	def display_lines(self):
		f = max(self._selected - self.max_lines/2, 0)
		f = min(len(self._lines) - self.max_lines, f)
		return self._lines[f:f+self.max_lines]

	def input(self):
		c = self._window.getch()

		if c == curses.KEY_DOWN:
			self._selected = min(len(self._lines) - 1, self._selected + 1)
		elif c == curses.KEY_UP:
			self._selected = max(0, self._selected - 1)
		elif c == curses.KEY_PPAGE:
			self._selected = max(0, self._selected - self.height/2)
		elif c == curses.KEY_NPAGE:
			self._selected = min(len(self._lines) - 1, self._selected + self.height/2)
		elif c == ord('\n'):
			self._callback(self, self._lines[self._selected], self._selected)
