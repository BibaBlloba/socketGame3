import curses
from time import sleep

from objects.Player import Player
from UI.CameraWindow import CameraWindow


class TestGameClient:
    def __init__(self) -> None:
        self.height, self.width = 0, 0
        self.game_state = {
            'player': {'id': 0, 'name': None, 'x': 0, 'y': 0},
            'objects': {'players': []},
            'chat': [],
            'last_message': None,
            'map': None,
        }
        self.camera = None
        self.player = None

        # WARNING: Игроки для отладки. Потом нужно получать его из Websocket.
        self.player = Player(
            player_id=1, x=0, y=0, name='Akeka', is_current_player=True
        )
        self.game_state['player'] = self.player
        test_player = Player(
            player_id=2, x=4, y=5, name='Xuilishe', is_current_player=False
        )
        self.game_state['objects']['players'].append(
            Player(player_id=2, x=-2, y=-3, name='Bob3', is_current_player=False)
        )
        self.game_state['objects']['players'].append(test_player)

    def RenderPlayer(self, player: Player):
        """Отрисовывает игрока в окне камеры."""
        if self.camera and self.camera.is_visible(player.x, player.y):
            # Определяем атрибуты отрисовки
            attr = curses.A_BOLD if player.is_current_player else curses.A_NORMAL

            self.camera.draw_char(player.skin, player.x, player.y, attr)

            # Отрисовываем имя игрока под ним, если есть место
            if self.camera.is_visible(player.x, player.y + 1):
                try:
                    name_x, name_y = self.camera.world_to_screen(player.x, player.y + 1)
                    name_display = player.name[:5]  # Ограничиваем длину имени
                    self.camera.win.addstr(
                        name_y, name_x - len(name_display) // 2, name_display
                    )
                except curses.error:
                    pass

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

    def renderCamera(self, stdscr: curses.window) -> None:
        """Отрисовывает окно камеры с игровым миром, игроком, и со всеми объектами."""
        if self.camera is None:
            cam_width = int(self.width * 0.7)
            cam_height = int(self.height * 0.9)
            self.camera = CameraWindow(stdscr, 1, 1, cam_width, cam_height)

        self.camera.clear()
        self.camera.draw_border()
        self.RenderPlayer(self.player)
        for player in self.game_state['objects']['players']:
            self.RenderPlayer(player)
        self.camera.refresh()

    def renderUI(self, stdscr) -> None:
        self.renderChat()
        self.renderCamera(stdscr)

    def renderFrame(self, stdscr: curses.window) -> None:
        self.height, self.width = stdscr.getmaxyx()

        self.renderUI(stdscr)

        stdscr.refresh()

    def add_chat_message(self, message: str):
        """Добавляет сообщение в чат и ограничивает количество сообщений"""
        self.game_state['chat'].append(str(message))
        if len(self.game_state['chat']) > 10:
            self.game_state['chat'].pop(0)

    def main(self, stdscr: curses.window) -> None:
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(0)
        frame = 0

        while True:
            sleep(0.01)
            frame += 1
            if frame % 6 == 0:
                self.game_state['objects']['players'][1].move(1, 0)
            self.renderFrame(stdscr)


if __name__ == '__main__':
    testGameClient = TestGameClient()
    curses.wrapper(testGameClient.main)
