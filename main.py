from curses import wrapper
from curses_app import CursesApp


def main(stdscr):
    stdscr.clear()
    CursesApp(stdscr)


if __name__ == '__main__':
    wrapper(main)
