# memcurses

memcurses is an ncurses application that lets you explore the memory of a running process.
Currently, it just supports viewing memory starting from a certain location.

## Usage

Launch memcurses with a PID and an address.
In modern Linuxes, you'll probably have to run this as root.

```bash
sudo python -m memcurses 29725 0x7fc57326a000
```

To explore memory, use `Up`, `Down`, `Left`, `Right`, `PgUp`, `PgDn`
To close the current window, press `Escape`.
To quit the program, press `Q`.

In the memory view, pointers to other pages (actually, page groups from `/proc/pid/maps`) are displayed in blue, and pointers to the same page are shown in green.
Or maybe the other way around...

## Future Work

If I have some time (or someone wants something to do), the current plans are:

- `Enter`-to-follow pointers
- struct view
- memory/struct saving (to flat file, or to python file)
- gdb support
- remote gdb support
