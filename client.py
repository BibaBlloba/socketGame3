import curses
import socket
import time
from curses.textpad import Textbox, rectangle
from turtle import clear


def draw_title(stdscr: curses.window, text: str):
    _, width = stdscr.getmaxyx()
    border_wing = f'{"═" * (width // 2 - len(text) * 2)}'
    title_win = curses.newwin(1, width, 0, 0)
    title_win.clear()
    title_win.addstr(0, 0, f'╒{border_wing} {text} {border_wing}╕')
    title_win.refresh()


def main(stdscr: curses.window):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8080))

    stdscr.addstr('keka')
    stdscr.refresh()

    draw_title(stdscr, 'azui')

    class player:
        x: int = 10
        y: int = 10

    world_window = curses.newwin(30, 60, 2, 2)
    world_window.addstr(player.x, player.y, '@')

    stdscr.nodelay(True)
    curses.curs_set(0)

    rectangle(stdscr, 2, 65, 29, 85)
    rectangle(stdscr, 30, 65, 32, 85)
    chat_text_window = curses.newwin(1, 19, 31, 66)
    box = Textbox(chat_text_window)
    stdscr.refresh()

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
    world_window.refresh()
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
            case 'KEY_ENTER' | '\n':
                box.edit()
                _text = box.gather()
                world_window.refresh()

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
