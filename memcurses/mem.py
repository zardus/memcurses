import re

class MemError(Exception): pass

class Page(object):
    def __init__(self, line):
        m = re.match(r'^([0-9A-Fa-f]+)-([0-9A-Fa-f]+) ([-r])([-w])([-x])([ps]) ([0-9A-Fa-f]+) ([^ ]*) ([^ ]*) *([^ ]*)$', line)
        self.start = int(m.group(1), 16)
        self.end = int(m.group(2), 16)
        self.r = m.group(3) == 'r'
        self.w = m.group(4) == 'w'
        self.x = m.group(5) == 'x'
        self.shared = m.group(6) == 'p'
        self.offset = int(m.group(7), 16)
        self.device = m.group(8)
        self.inode = m.group(9)
        self.path = m.group(10)
        self.str = line

    @property
    def size(self):
        return self.end - self.start

class Mem(object):
    def __init__(self, pid=None):
        self._pid = pid
        if pid is not None:
            self._mem_file = open('/proc/%s/mem' % pid)

    def read(self, base, length):
        self._mem_file.seek(base)
        try:
            data = self._mem_file.read(length)
            return data
        except IOError:
            raise MemError("out of bounds")

    @property
    def maps(self):
        return [ Page(line.strip()) for line in open("/proc/%s/maps" % self._pid) ]

    def container(self, addr, maps=None):
        maps = self.maps if maps is None else maps

        for p in maps:
            if p.start <= addr and p.end > addr:
                return p
        return None
