import curses
from . import MemCurses

def main(screen):
    import sys
    pid = sys.argv[1]
    start_addr = int(sys.argv[2], 16)

    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)

    mc = MemCurses(screen, pid=pid, start_addr=start_addr)
    mc.interact()

if __name__ == '__main__':
    curses.wrapper(main)
