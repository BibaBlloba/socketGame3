import curses
from time import sleep


class TestGameClient:
    def __init__(self) -> None:
        self.height, self.width = 0, 0
        self.game_state = {
            'player': {'id': 0, 'name': None, 'x': 0, 'y': 0},
            'objects': {'players': {}},
            'chat': [],
            'last_message': None,
            'map': None,
        }

    def renderChat(self) -> None:
        chat_width = 30
        if self.height >= 30:
            chat_height = 30
        else:
            chat_height = self.height - 5
        chat_x = self.width - chat_width - 1
        chat_y = 1

        # Рисуем рамку чата
        chat_win = curses.newwin(chat_height, chat_width, chat_y, chat_x)
        chat_win.box()
        chat_win.addstr(0, 2, ' Чат ')

        # Доступная высота для сообщений (исключая рамку)
        available_height = chat_height - 2
        max_line_width = chat_width - 2  # Ширина с учетом отступов от рамки

        # Собираем все строки для отображения
        display_lines = []

        # Обрабатываем сообщения в прямом порядке (от старых к новым)
        for msg in self.game_state['chat']:
            # Разбиваем длинные сообщения на несколько строк
            if len(msg) <= max_line_width:
                display_lines.append(msg)
            else:
                # Разбиваем сообщение на строки нужной длины
                start = 0
                while start < len(msg):
                    end = start + max_line_width
                    if end < len(msg):
                        # Пытаемся найти пробел для разрыва слова
                        break_pos = msg.rfind(' ', start, end)
                        if break_pos != -1 and break_pos > start:
                            end = break_pos + 1

                    display_lines.append(msg[start:end].strip())
                    start = end

        # Берем только последние N строк, которые помещаются в чат
        visible_lines = display_lines[-available_height:]

        # Отображаем строки (первые строки вверху, последние внизу)
        for i, line in enumerate(visible_lines):
            if i < available_height:
                chat_win.addstr(i + 1, 1, line.ljust(max_line_width)[:max_line_width])

        chat_win.refresh()

    def renderUI(self) -> None:
        self.renderChat()

    def renderFrame(self, stdscr: curses.window) -> None:
        self.height, self.width = stdscr.getmaxyx()

        self.renderUI()

        stdscr.refresh()

    def main(self, stdscr: curses.window) -> None:
        curses.start_color()
        curses.use_default_colors()
        frame = 0

        while True:
            sleep(0.01)
            frame += 1
            self.renderFrame(stdscr)


if __name__ == '__main__':
    testGameClient = TestGameClient()
    curses.wrapper(testGameClient.main)
