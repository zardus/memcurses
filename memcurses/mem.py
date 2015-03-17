class MemError(Exception): pass

class Mem(object):
    def __init__(self, pid=None):
        if pid is not None:
            self._mem_file = open('/proc/%d/mem' % int(pid))

    def read(self, base, length):
        self._mem_file.seek(base)
        try:
            data = self._mem_file.read(length)
            return data
        except IOError:
            raise MemError("out of bounds")
