import curses
from . import MemCurses

def main():
    import sys
    pid = int(sys.argv[1])
    start_addr = int(sys.argv[2], 16)

    try:
        mc = MemCurses(pid=pid, start_addr=start_addr)
        mc.interact()
    finally:
        curses.endwin()

if __name__ == '__main__':
    main()
