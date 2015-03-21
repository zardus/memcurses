import curses
import struct
import string

import logging
l = logging.getLogger('memcurses.memview')
#l.setLevel(logging.DEBUG)

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

	#
	# Various properties to help with laying stuff out
	#

	@property
	def words_per_row(self):
		total_width = self.width - self.first_mem_column

		per_byte_ratio = float(self.word_char_cost) / self._word_size
		bytes_per_row = int(total_width / per_byte_ratio)
		words_per_row = bytes_per_row / self._word_size

		return words_per_row

	@property
	def word_separator_size(self):
		wss = 1 if self._word_size > 1 else 0
		return wss

	@property
	def word_char_cost(self):
		# 2 bytes for hex-encoded, 1 for byte separator, 1 for ascii display, and maybe 1 for word separator
		wcc = 4 * self._word_size + self.word_separator_size
		return wcc

	@property
	def hex_word_size(self):
		# 2 bytes for hex-encoded, 1 for byte separator, and maybe 1 for word separator
		hws =  3 * self._word_size + self.word_separator_size
		return hws

	@property
	def max_rows(self):
		return self.height

	@property
	def displayable_amount(self):
		da = self.max_rows * self.words_per_row * self._word_size
		return da

	@property
	def min_display_addr(self):
		return self._addr

	@property
	def max_display_addr(self):
		return self.min_display_addr + self.displayable_amount

	@property
	def first_mem_column(self): #pylint:disable=no-self-use
		return struct.calcsize("P")*2 + 2

	@property
	def first_ascii_column(self):
		return self.first_mem_column + self.hex_word_size*self.words_per_row

	@property
	def bytes_per_row(self):
		bpr = self.words_per_row * self._word_size
		return bpr

	#
	# Functionality used in drawing
	#

	def _points_to(self, offset):
		s = struct.calcsize("P")
		if offset + s > len(self._data):
			return False

		container = self._mc._mem.container(struct.unpack("P", self._data[offset:offset+s])[0], maps=self._mc._maps)

		if container is None: return None
		elif container.start <= self._addr+offset and container.end > self._addr+offset: return MemViewAddr._POINTS_US
		else: return MemViewAddr._POINTS_OTHER

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

	def _display_ascii(self):
		for i in range(len(self._data)):
			row = i / self.bytes_per_row
			column = self.first_ascii_column + i % self.bytes_per_row

			to_display = string.digits + string.letters + ' '
			a = ord(self._data[i]) if self._data[i] in to_display else curses.ACS_BULLET #pylint:disable=no-member
			color = self._data_colors[i]

			#l.debug('(%d,%d) of (%d,%d) is %r', row, column, self.height, self.width, repr(a))
			try: self._window.addch(row, column, a, color)
			except curses.error: pass

	def _display_byte(self, i):
		byte = self._data[i]
		color = self._data_colors[i]

		row = i / (self.words_per_row * self._word_size)
		word_in_column = i % (self.words_per_row * self._word_size)
		interword_spacing_ratio = float(self.hex_word_size)/(self._word_size*3)
		column = int(interword_spacing_ratio * (word_in_column * 3))

		self._window.addstr(row, self.first_mem_column + column, byte.encode('hex'), color)

	def _display_mem(self):
		for i in range(len(self._data)):
			self._display_byte(i)

		self._shown = self._data
		self._shown_colors = self._data_colors

	def _display_addrs(self):
		s = struct.calcsize("P")
		for i in range(self.height):
			addr = self._addr + i*self.words_per_row*self._word_size
			self._window.addstr(i, 0, ("%x" % addr).zfill(s*2))

	#
	# View API
	#

	def draw(self):
		#self._window.clear()

		l.debug("About to draw")
		l.debug("height: %d", self.height)
		l.debug("width: %d", self.width)
		l.debug("words per row: %d", self.words_per_row)
		l.debug("word separator size: %d", self.word_separator_size)
		l.debug("word char cost: %d", self.word_char_cost)
		l.debug("hex word size: %d", self.hex_word_size)
		l.debug("displayable amount: %d", self.displayable_amount)
		l.debug("bytes per row: %d", self.bytes_per_row)

		l.debug("refreshing data")
		self._refresh_data()
		l.debug("displaying addresses")
		self._display_addrs()
		l.debug("displaying hex memory")
		self._display_mem()
		l.debug("displaying ascii memory")
		self._display_ascii()
		self._window.noutrefresh()

	def input(self):
		selection_moved = False

		old_selection = self._selected
		old_addr = self._addr

		c = self._window.getch()
		if c == curses.KEY_DOWN:
			self._addr += self.words_per_row * self._word_size
		elif c == curses.KEY_UP:
			self._addr -= self.words_per_row * self._word_size
		elif c == curses.KEY_LEFT:
			self._addr -= self._word_size
		elif c == curses.KEY_RIGHT:
			self._addr += self._word_size
		elif c == ord('['):
			self._addr -= 1
		elif c == ord(']'):
			self._addr += 1
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
		elif c in [ 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38 ]:
			self._word_size = c - 0x30
			self._window.clear()
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

		if self._mc._mem.container(self._addr, maps=self._mc._maps) is None:
			err = MemViewMessage(curses.newwin(1, 1), self._mc, "Error", [ "Memory at address 0x%x is not mapped." % self._addr ])
			self._selected = old_selection
			self._addr = old_addr
			return err


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
