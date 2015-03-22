import logging
l = logging.getLogger('memcurses.memview')
#l.setLevel(logging.DEBUG)

class MemView(object):
	def __init__(self, memcurses, window=None):
		if window is not None:
			self._window = window
		else:
			self._window = memcurses._screen.subwin(memcurses.height, memcurses.width, 0, 0)
			self._window.clear()

		self._mc = memcurses
		self._x = 0
		self._y = 0
		self._closed = False

		self._window.nodelay(True)
		self._window.keypad(True)

	@property
	def width(self):
		return self._window.getmaxyx()[1]

	@property
	def height(self):
		return self._window.getmaxyx()[0]

	#
	# the API
	#

	def draw(self):
		raise NotImplementedError()

	def input(self):
		raise NotImplementedError()

	def close(self):
		self._closed = True
