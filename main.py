import curses
import time


def draw_title(stdscr: curses.window, text: str):
    _, width = stdscr.getmaxyx()
    border_wing = f'{"═" * (width // 2 - (len(text)))}'
    title_win = curses.newwin(1, width, 0, 0)
    title_win.clear()
    title_win.addstr(0, 0, f'╒{border_wing} {text} {border_wing}╕')
    title_win.refresh()


def main(stdscr: curses.window):
    counter_window = curses.newwin(10, 10, 10, 10)
    stdscr.addstr('keka')
    stdscr.refresh()

    draw_title(stdscr, 'azui')

    pad = curses.newpad(100, 100)
    for i in range(100):
        for j in range(26):
            char = chr(67 + j)
            pad.addstr(char)

    stdscr.getch()


curses.wrapper(main)
