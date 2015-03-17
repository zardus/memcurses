import curses
import struct

class MemView(object):
	def __init__(self, window, memcurses):
		self._window = window
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

class MemViewAddr(MemView):
	_POINTS_US = 1
	_POINTS_OTHER = 2

	def __init__(self, window, memcurses, addr, word_size=None):
		MemView.__init__(self, window, memcurses)
		self._addr = addr
		self._selected = addr
		self._word_size = struct.calcsize("P") if word_size is None else word_size

	@property
	def words_per_row(self):
		row_words = self.width / (self._word_size*3 + 1)
		if self.width - row_words * (self._word_size*3 + 1) >= self._word_size*3:
			row_words += 1
		return row_words

	@property
	def max_rows(self):
		return self.height

	@property
	def displayable_amount(self):
		return self.max_rows * self.words_per_row * self._word_size

	@property
	def mem_contents(self):
		return self._mc._mem.read(self._addr, self.displayable_amount)

	@property
	def min_display_addr(self):
		return self._addr

	@property
	def max_display_addr(self):
		return self.min_display_addr + self.displayable_amount

	def _points_to(self, data, offset):
		s = struct.calcsize("P")
		if offset + s > len(data):
			return False
		container = self._mc._mem.container(struct.unpack("P", data[offset:offset+s])[0], maps=self._mc._maps)
		if container is None:
			return None
		elif container.start <= self._addr+offset and container.end > self._addr+offset:
			return MemViewAddr._POINTS_US
		else:
			return MemViewAddr._POINTS_OTHER

	def _display_mem(self, data):
		cur_color = None

		i = 0
		for y in range(self.max_rows):
			cur_x = 0
			for _ in range(self.words_per_row):
				byte_type = self._points_to(data, i)

				for w in range(self._word_size):
					if self._addr + i == self._selected: color = curses.color_pair(2)
					elif byte_type == MemViewAddr._POINTS_US: color = curses.color_pair(4)
					elif byte_type == MemViewAddr._POINTS_OTHER: color = curses.color_pair(5)
					else: color = curses.color_pair(0)

					self._window.addstr(y, cur_x+w*3, data[i].encode('hex'), color)
					i += 1

				cur_x += 3*self._word_size + 1

	def draw(self):
		self._window.clear()
		self._display_mem(self.mem_contents)
		self._window.noutrefresh()

	def input(self):
		c = self._window.getch()
		selection_moved = False

		if c == curses.KEY_DOWN:
			self._addr += self.words_per_row * self._word_size
		elif c == curses.KEY_UP:
			self._addr -= self.words_per_row * self._word_size
		elif c == curses.KEY_LEFT:
			self._addr -= self._word_size
		elif c == curses.KEY_RIGHT:
			self._addr += self._word_size
		elif c == curses.KEY_NPAGE:
			self._addr += self.words_per_row * self._word_size * self.height/2
		elif c == curses.KEY_PPAGE:
			self._addr -= self.words_per_row * self._word_size * self.height/2
		elif c in ( ord('W'), ord('w')):
			self._selected -= self.words_per_row * self._word_size
			selection_moved = True
		elif c in ( ord('S'), ord('s')):
			self._selected += self.words_per_row * self._word_size
			selection_moved = True
		elif c == ord('d'):
			self._selected += 1
			selection_moved = True
		elif c == ord('a'):
			self._selected -= 1
			selection_moved = True
		elif c == ord('D'):
			self._selected += self._word_size
			selection_moved = True
		elif c == ord('A'):
			self._selected -= self._word_size
			selection_moved = True
		else:
			curses.ungetch(c)
			return False

		if self._selected > self.max_display_addr and selection_moved:
			self._addr += self.words_per_row * self._word_size
		elif self._selected < self.min_display_addr and selection_moved:
			self._addr -= self.words_per_row * self._word_size
		elif not selection_moved:
			while self._selected > self.max_display_addr:
				self._selected -= self.words_per_row * self._word_size
			while self._selected < self.min_display_addr:
				self._selected += self.words_per_row * self._word_size

class MemViewHelp(MemView):
	def draw(self):
		pass

	def input(self):
		pass
