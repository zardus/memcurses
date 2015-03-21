import logging
l = logging.getLogger('memcurses.views.message')
#l.setLevel(logging.DEBUG)

from ..memview import MemView

class MemViewMessage(MemView):
	def __init__(self, window, memcurses, subject, lines):
		MemView.__init__(self, window, memcurses)

		win_width = min(memcurses.width, max(max(len(line) for line in lines), len(subject)) + 4)
		win_height = min(memcurses.height, len(lines) + 6)

		x = (memcurses.width - win_width) / 2
		y = (memcurses.height - win_height) / 2

		l.debug("Message window going to %dx%d+%d+%d", win_height, win_width, y, x)
		window.mvwin(y, x)
		window.resize(win_height, win_width)

		self._subject = subject
		self._lines = lines

	def _draw_line(self, y, line, centered=False):
		w = min(len(line), self.width)

		if centered: x = (self.width - w) / 2
		else: x = 2

		self._window.addstr(y, x, line[:self.width-x-2])

	def draw(self):
		self._window.erase()
		self._window.border(0)

		self._draw_line(2, self._subject, centered=True)
		for y,line in enumerate(self._lines[:self.height - 4]):
			self._draw_line(y+4, line)

		self._window.noutrefresh()

	def input(self):
		c = self._window.getch()
		l.debug("%r ignoring key %r", self, c)
		return None
