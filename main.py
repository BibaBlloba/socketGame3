import curses
import time
from turtle import clear


def draw_title(stdscr: curses.window, text: str):
    _, width = stdscr.getmaxyx()
    border_wing = f'{"═" * (width // 2 - len(text) * 2)}'
    title_win = curses.newwin(1, width, 0, 0)
    title_win.clear()
    title_win.addstr(0, 0, f'╒{border_wing} {text} {border_wing}╕')
    title_win.refresh()


def main(stdscr: curses.window):
    stdscr.addstr('keka')
    stdscr.refresh()

    draw_title(stdscr, 'azui')

    class player:
        x: int = 10
        y: int = 10

    world_window = curses.newwin(30, 30, 2, 2)
    world_window.addstr(player.x, player.y, '@')

    stdscr.nodelay(True)
    curses.curs_set(0)

    frame = 0
    while True:
        frame += 1
        time.sleep(0.001)
        stdscr.addstr(1, 1, f'frame: {frame}')
        try:
            key = stdscr.getkey()
        except:
            continue
        match key:
            case 'q':
                exit()
            case 'KEY_LEFT' | 'a':
                player.x -= 1
            case 'KEY_RIGHT' | 'd':
                player.x += 1
            case 'KEY_UP' | 'w':
                player.y -= 1
            case 'KEY_DOWN' | 's':
                player.y += 1

        world_window.clear()
        world_window.border(
            curses.ACS_VLINE,
            curses.ACS_VLINE,
            curses.ACS_HLINE,
            curses.ACS_HLINE,
            curses.ACS_ULCORNER,
            curses.ACS_URCORNER,
            curses.ACS_LLCORNER,
            curses.ACS_LRCORNER,
        )
        world_window.addstr(2, 2, f'Key: {key}'.ljust(20))
        world_window.addstr(player.y, player.x, '@')
        world_window.refresh()


curses.wrapper(main)
