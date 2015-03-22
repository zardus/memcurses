import curses
import struct
import string

from ..memview import MemView

import logging
l = logging.getLogger('memcurses.views.hex')
#l.setLevel(logging.DEBUG)

class MemViewHex(MemView):
	_POINTS_US = 1
	_POINTS_OTHER = 2

	def __init__(self, memcurses, mapping, addr=None, window=None, word_size=None):
		MemView.__init__(self, memcurses, window=window)
		self._mapping = mapping
		self._addr = mapping.start if addr is None else addr
		self._selected = self._addr
		self._word_size = struct.calcsize("P") if word_size is None else word_size

		self._data = [ ]
		self._data_colors = [ ]

		self._selections = [ ]

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
		elif container.start <= self._addr+offset and container.end > self._addr+offset: return MemViewHex._POINTS_US
		else: return MemViewHex._POINTS_OTHER

	def _refresh_data(self):
		self._data = self._mc._mem.read(self._addr, self.displayable_amount)
		self._data_colors = [ ]

		same_color_bytes = 0
		last_color = None
		for i in range(len(self._data)):
			byte_type = self._points_to(i)

			if same_color_bytes > 0:
				self._data_colors.append(last_color)
			elif byte_type == MemViewHex._POINTS_US:
				last_color = curses.color_pair(4)
				self._data_colors.append(last_color)
				same_color_bytes = 8
			elif byte_type == MemViewHex._POINTS_OTHER:
				last_color = curses.color_pair(5)
				self._data_colors.append(last_color)
				same_color_bytes = 8
			else:
				last_color = curses.color_pair(0)
				self._data_colors.append(last_color)

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

		if self._addr + i == self._selected:
			#self._data_colors[-1] = curses.color_pair(2)
			color |= curses.A_STANDOUT

		self._window.addstr(row, self.first_mem_column + column, byte.encode('hex'), color)

	def _display_mem(self):
		for i in range(len(self._data)):
			self._display_byte(i)

	def _display_addrs(self):
		s = struct.calcsize("P")
		for i in range(self.height):
			addr = self._addr + i*self.words_per_row*self._word_size
			self._window.addstr(i, 0, ("%x" % addr).zfill(s*2))

	#
	# View API
	#

	def draw(self):
		self._window.erase()

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
		selection_jumped = False

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
		elif c == curses.KEY_HOME:
			self._addr = self._mapping.start
		elif c == curses.KEY_END:
			self._addr = self._mapping.end - self.bytes_per_row*self.height
		elif c == ord('['):
			self._addr -= 1
		elif c == ord(']'):
			self._addr += 1
		elif c == curses.KEY_NPAGE:
			self._addr += self.bytes_per_row * (self.height/2)
		elif c == curses.KEY_PPAGE:
			self._addr -= self.bytes_per_row * (self.height/2)
		elif c == ord('w'):
			self._selected -= self.bytes_per_row
			selection_moved = True
		elif c == ord('W'):
			self._selected -= self.bytes_per_row * (self.height/2)
			selection_moved = True
		elif c == ord('s'):
			self._selected += self.bytes_per_row
			selection_moved = True
		elif c == ord('S'):
			self._selected += self.bytes_per_row * (self.height/2)
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
		elif c == ord('\n'):
			ptr = self._data[self._selected - self._addr:self._selected - self._addr + self._mc._mem.word_size]
			if len(ptr) == self._mc._mem.word_size:
				self._selected = struct.unpack("P", ptr)[0]
				self._selections.append(old_selection)
				selection_jumped = True
		elif c == 27:
			if len(self._selections) != 0:
				self._selected = self._selections.pop()
				selection_jumped = True

		selected_row = (self._selected - self._addr) / self.bytes_per_row
		old_selected_column = (self._selected - old_addr) % self.bytes_per_row

		if selection_moved and selected_row < 0:
			self._addr += selected_row * self.bytes_per_row
		elif selection_moved and selected_row >= self.height:
			self._addr += (selected_row-self.height+1) * self.bytes_per_row
		elif selection_jumped and (selected_row < -1 or selected_row > self.height):
			self._addr = self._selected
		elif not selection_moved and selected_row < 0:
			self._selected = self._addr + old_selected_column
		elif not selection_moved and selected_row >= self.height:
			self._selected = self._addr + self.bytes_per_row*(self.height-1) + old_selected_column

		if self._mc._mem.container(self._addr, maps=self._mc._maps) is None:
			err = MemViewMessage(self._mc, "Error", [ "Memory at address 0x%x is not mapped (trying to display selection 0x%x)." % (self._addr, self._selected) ])
			self._selected = old_selection
			self._addr = old_addr
			return err

from .message import MemViewMessage
