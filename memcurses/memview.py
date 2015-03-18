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

		self._data = [ ]
		self._data_colors = [ ]

		self._shown = [ ]
		self._shown_colors = [ ]

	def _refresh_data(self):
		self._data = self._mc._mem.read(self._addr, self.displayable_amount)
		self._data_colors = [ ]

		same_color_bytes = 0
		for i in range(len(self._data)):
			byte_type = self._points_to(i)

			if self._addr + i == self._selected:
				self._data_colors.append(curses.color_pair(2))
			elif same_color_bytes > 0:
				self._data_colors.append(self._data_colors[-1])
			elif byte_type == MemViewAddr._POINTS_US:
				self._data_colors.append(curses.color_pair(4))
				same_color_bytes = 8
			elif byte_type == MemViewAddr._POINTS_OTHER:
				self._data_colors.append(curses.color_pair(5))
				same_color_bytes = 8
			else:
				self._data_colors.append(curses.color_pair(0))
			same_color_bytes -= 1

	@property
	def words_per_row(self):
		total_width = self.width - self.first_mem_column

		row_words = total_width / (self._word_size*3 + 1)
		if total_width - row_words * (self._word_size*3 + 1) >= self._word_size*3:
			row_words += 1

		return row_words

	@property
	def max_rows(self):
		return self.height

	@property
	def displayable_amount(self):
		return self.max_rows * self.words_per_row * self._word_size

	@property
	def min_display_addr(self):
		return self._addr

	@property
	def max_display_addr(self):
		return self.min_display_addr + self.displayable_amount

	@property
	def first_mem_column(self): #pylint:disable=no-self-use
		return struct.calcsize("P")*2 + 2

	def _points_to(self, offset):
		s = struct.calcsize("P")
		if offset + s > len(self._data):
			return False

		container = self._mc._mem.container(struct.unpack("P", self._data[offset:offset+s])[0], maps=self._mc._maps)

		if container is None: return None
		elif container.start <= self._addr+offset and container.end > self._addr+offset: return MemViewAddr._POINTS_US
		else: return MemViewAddr._POINTS_OTHER

	def _display_byte(self, i):
		byte = self._data[i]
		color = self._data_colors[i]

		row = i / (self.words_per_row * self._word_size)
		word_in_column = i % (self.words_per_row * self._word_size)
		interword_spacing = float(self._word_size*3+1)/(self._word_size*3)
		column = int(interword_spacing * (word_in_column * 3))

		self._window.addstr(row, self.first_mem_column + column, byte.encode('hex'), color)

	def _display_mem(self):
		for i in range(len(self._data)):
			self._display_byte(i)

		self._shown = self._data
		self._shown_colors = self._data_colors

	def _display_addrs(self):
		for i in range(self.height):
			addr = self._addr + i*self.words_per_row*self._word_size
			self._window.addstr(i, 0, ("%x" % addr).zfill(self._word_size*2))

	def draw(self):
		#self._window.clear()
		self._refresh_data()
		self._display_addrs()
		self._display_mem()
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
