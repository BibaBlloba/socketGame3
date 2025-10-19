import argparse
import asyncio
import curses
import threading
from curses import newwin, textpad
from queue import Queue
from random import random

import requests
import websockets

from engine.GameProtocol import (GameProtocol, MessageType, PlayerInit,
                                 PlayerJoin, PlayerUpdate)

SERVER_IP: str


class LoginForm:
    def __init__(self) -> None:
        pass

    def run(self) -> str:
        def main(stdscr: curses.window):
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(4, curses.COLOR_RED, -1)

            while True:
                height, width = stdscr.getmaxyx()
                message_win = newwin(6, 20, height // 2 + 4, width // 2 - 10)
                message_win.box()
                try:
                    response = requests.get(f'http://{SERVER_IP}:8000/status')
                except Exception as ex:
                    message_win.addstr(1, 1, 'Сервер недоступен', curses.color_pair(4))
                    message_win.addstr(4, 5, '𓍊𓋼𓍊𓋼𓍊𓆏 𓍊𓋼𓍊𓋼𓍊')
                    message_win.refresh()

                login, password = self.login_screen(stdscr)

                try:
                    response = requests.post(
                        f'http://{SERVER_IP}:8000/auth/login',
                        json={'name': login, 'password': password},
                    )
                    if response.status_code == 200:
                        return response.json()['access_token']
                    else:
                        message_win.addstr(1, 1, f'{response.json()["detail"]}')
                        message_win.addstr(4, 5, '𓍊𓋼𓍊𓋼𓍊𓆏 𓍊𓋼𓍊𓋼𓍊')
                        message_win.refresh()
                except Exception as ex:
                    raise ex

        return curses.wrapper(main)

    def login_screen(self, stdscr):
        curses.curs_set(1)
        stdscr.keypad(True)
        height, width = stdscr.getmaxyx()

        login_win = curses.newwin(6, 40, height // 2 - 3, width // 2 - 20)
        login_win.box()
        login_win.addstr(0, 2, ' Login ')

        login_win.addstr(1, 2, 'Username: ')
        login_win.addstr(3, 2, 'Password: ')

        username_field = curses.newwin(1, 25, height // 2 - 2, width // 2 - 8)
        password_field = curses.newwin(1, 25, height // 2, width // 2 - 8)

        username_textbox = textpad.Textbox(username_field)
        password_textbox = textpad.Textbox(password_field)

        current_field = 0  # 0 - username, 1 - password
        fields = [username_textbox, password_textbox]
        login_win.refresh()
        username_field.refresh()
        password_field.refresh()

        while True:
            if current_field == 0:
                username_field.refresh()
                # Кастомный обработчик для username
                username_textbox.edit(self.enter_handler)
                current_field = 1
            else:
                password_field.refresh()
                # Кастомный обработчик для password
                password_textbox.edit(self.enter_handler)
                # После ввода пароля - завершаем
                break

            login_win.refresh()

        username = username_textbox.gather().strip()
        password = password_textbox.gather().strip()

        return username, password

    def enter_handler(self, key):
        """Обработчик клавиш для Textbox.
        Enter переходит к следующему полю, Ctrl+G завершает ввод."""
        if key == curses.KEY_ENTER or key in (10, 13):  # Enter
            return 7  # Ctrl+G - завершает редактирование текущего поля
        elif key == curses.KEY_BTAB:  # Shift+Tab - возврат к предыдущему полю
            return 7
        return key


class GameClient:
    def __init__(self, server_url: str, token: str) -> None:
        self.player_id: int = None
        self.player_name: int = None
        self.server_url = f'ws://{server_url}:8000/game/ws?token={token}'
        self.game_state = {
            'player': {'id': 0, 'name': None, 'x': 0, 'y': 0},
            'objects': {'players': {}},
            'chat': [],
            'last_message': None,
            'map': None,
        }
        self.message_queue = Queue()
        self.outgoing_queue = Queue()
        self.websocket = None

        # FIX: For testing
        self.game_state['map'] = self.create_large_map(80, 40)

    # Генерация большой карты для тестирования скроллинга
    def create_large_map(self, width=100, height=50):
        map_data = []

        # Верхняя граница
        map_data.append(list('#' * width))

        # Средние строки
        for y in range(1, height - 1):
            row = ['#']  # Левая граница
            for x in range(1, width - 1):
                # Случайные препятствия (10% chance)
                if random() < 0.1:
                    row.append('#')
                else:
                    row.append('.')
            row.append('#')  # Правая граница
            map_data.append(row)

        # Нижняя граница
        map_data.append(list('#' * width))

        return map_data

    async def websocket_listener(self):
        """Прослушивание сообщений от сервера и отправка исходящих"""
        try:
            async with websockets.connect(self.server_url) as ws:
                self.websocket = ws

                send_task = asyncio.create_task(self.outgoing_sender())

                message = await ws.recv()
                self.message_queue.put(message)

                try:
                    while True:
                        message = await ws.recv()
                        # self.add_chat_message(GameProtocol.unpack_message(message))
                        self.message_queue.put(message)
                finally:
                    send_task.cancel()
                    await send_task
        except Exception as e:
            print(f'WebSocket error: {e}')
            self.running = False

    async def outgoing_sender(self):
        """Отправка исходящих сообщений из очереди"""
        while True:
            try:
                # Ждем сообщение для отправки
                message = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.outgoing_queue.get,
                    True,
                    0.1,  # timeout 0.1s
                )
                if self.websocket:
                    await self.websocket.send(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                pass

    def process_server_messages(self):
        """Обработка сообщений от сервера (вызывается в основном потоке)"""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.handle_server_message(message)

    def handle_server_message(self, message: bytes):
        """Разбор сообщений от сервера"""
        msg_type, data = GameProtocol.unpack_message(message)

        try:
            match msg_type:
                case MessageType.PLAYER_INIT:
                    self.player_id = data.player_id
                    self.player_name = data.name
                    self.game_state['player'] = {
                        'id': data.player_id,
                        'name': data.name,
                        'x': data.x,
                        'y': data.y,
                    }
                case MessageType.PLAYER_JOIN:
                    self.game_state['last_message'] = 'player join'
                    self.add_chat_message(f'player join: {data.name}')
                    self.game_state['objects']['players'][data.player_id] = {
                        'name': data.name,
                        'x': data.x,
                        'y': data.y,
                    }
                case MessageType.PLAYER_UPDATE:
                    self.game_state['objects']['players'][data.player_id] = {
                        'name': data.name,
                        'x': data.x,
                        'y': data.y,
                    }
                case MessageType.PLAYER_LEAVE:
                    player = self.game_state['objects']['players'][data]
                    self.add_chat_message(f'player leave: {player["name"]}')
                    self.game_state['objects']['players'].pop(data, None)
        except Exception as e:
            raise e

        #     elif command == 'chat':
        #         # chat:player_id:message
        #         _, sender_id, msg_text = parts
        #         self.game_state['chat'].append(
        #             {'sender': sender_id, 'text': msg_text, 'time': time.time()}
        #         )
        #         # Держим только последние 10 сообщений
        #         if len(self.game_state['chat']) > 10:
        #             self.game_state['chat'] = self.game_state['chat'][-10:]
        #
        # except Exception as e:
        #     print(f"Error processing message '{message}': {e}")

    def send_chat_message(self, message: str):
        self.add_chat_message(message)

    def send_move(self, dx: int, dy: int):
        """Отправка движения на сервер"""
        try:
            new_x: int = self.game_state['player']['x'] + dx
            new_y: int = self.game_state['player']['y'] + dy

            # Обновляем локально для немедленного отклика
            self.game_state['player']['x'] = new_x
            self.game_state['player']['y'] = new_y

            message = GameProtocol.pack_player_update(
                PlayerUpdate(self.player_id, self.player_name, new_x, new_y)
            )
            self.outgoing_queue.put(message)

        except Exception as ex:
            raise ex

    def add_chat_message(self, message: str):
        """Добавляет сообщение в чат и ограничивает количество сообщений"""
        self.game_state['chat'].append(str(message))
        if len(self.game_state['chat']) > 10:
            self.game_state['chat'].pop(0)

    def render_chat(self, stdscr: curses.window):
        """Рендерит чат в правом верхнем углу экрана"""
        height, width = stdscr.getmaxyx()
        chat_width = 30
        chat_height = 30
        chat_x = width - chat_width - 1
        chat_y = 1

        # Рисуем рамку чата
        chat_win = curses.newwin(chat_height, chat_width, chat_y, chat_x)
        chat_win.box()
        chat_win.addstr(0, 2, ' Чат ')

        # Доступная высота для сообщений (исключая рамку)
        available_height = chat_height - 2
        max_line_width = chat_width - 2  # Ширина с учетом отступов от рамки

        textbox_win = newwin(
            3,
            chat_width - 2,
            chat_y + available_height + 2,
            chat_x + 1,
        )
        self.chat_field = textpad.Textbox(textbox_win)
        # _win = newwin(
        #     5,
        #     chat_width,
        #     chat_y + available_height + 1,
        #     chat_x,
        # )
        # _win.box()
        # _win.refresh()
        textbox_win.refresh()

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

    def render_map(self, stdscr: curses.window):
        height, width = stdscr.getmaxyx()
        player = self.game_state['player']

        # Центрируем камеру на игроке
        camera_x = player['x'] - width // 2
        camera_y = player['y'] - height // 2

        # Получаем карту из game_state
        if 'map' not in self.game_state:
            return

        game_map = self.game_state['map']
        if not game_map:
            return

        map_height = len(game_map)
        map_width = len(game_map[0]) if map_height > 0 else 0

        # Вычисляем центр карты в абсолютных координатах
        # Предполагаем, что центр карты находится в (0,0)
        # Тогда левый верхний угол карты будет в (-map_width//2, -map_height//2)
        map_center_x = 0
        map_center_y = 0
        map_start_x = map_center_x - map_width // 2
        map_start_y = map_center_y - map_height // 2
        map_end_x = map_start_x + map_width
        map_end_y = map_start_y + map_height

        # Рендерим видимую часть карты
        for screen_y in range(height):
            for screen_x in range(width):
                # Вычисляем абсолютные координаты мира
                world_x = camera_x + screen_x
                world_y = camera_y + screen_y

                # Преобразуем мировые координаты в координаты карты
                map_x = world_x - map_start_x
                map_y = world_y - map_start_y

                # Проверяем, находится ли точка в пределах карты
                if 0 <= map_y < map_height and 0 <= map_x < map_width:
                    char = game_map[map_y][map_x]

                    # Проверяем, что символ можно отобразить
                    if char and 32 <= ord(char) <= 126:
                        try:
                            curses.init_pair(2, curses.COLOR_CYAN, -1)
                            color_pair = curses.color_pair(2)
                        except Exception:
                            color_pair = 0
                        try:
                            stdscr.addch(screen_y, screen_x, char, color_pair)
                        except curses.error:
                            pass

                else:
                    # Если за пределами карты - рисуем пустоту
                    try:
                        stdscr.addch(screen_y, screen_x, ' ')
                    except curses.error:
                        pass

    def render(self, stdscr: curses.window, frame):
        # stdscr.clear()
        height, width = stdscr.getmaxyx()
        player = self.game_state['player']

        # Центрируем камеру на игроке
        camera_x = player['x'] - width // 2

        camera_y = player['y'] - height // 2

        self.render_map(stdscr)

        stdscr.addstr(0, 0, f'frame: {frame}')
        stdscr.addstr(0, 20, f'name: {self.game_state["player"]["name"]}')
        stdscr.addstr(1, 20, f'id: {self.player_id}')
        stdscr.addstr(0, 40, f'last_message: {self.game_state["last_message"]}')
        stdscr.addstr(1, 40, f'x: {self.game_state["player"]["x"]}')
        stdscr.addstr(2, 40, f'y: {self.game_state["player"]["y"]}')

        # Рисуем игрока
        player_screen_x = player['x'] - camera_x
        player_screen_y = player['y'] - camera_y
        if 0 <= player_screen_x < width and 0 <= player_screen_y < height:
            stdscr.addch(player_screen_y, player_screen_x, '@')

        if 'objects' in self.game_state and 'players' in self.game_state['objects']:
            for other_player_id, other_player in self.game_state['objects'][
                'players'
            ].items():
                if other_player_id == self.player_id:
                    continue

                # Преобразуем абсолютные координаты в экранные относительно камеры
                other_screen_x = other_player['x'] - camera_x
                other_screen_y = other_player['y'] - camera_y

                # Проверяем, виден ли игрок на экране
                if 0 <= other_screen_x < width and 0 <= other_screen_y < height:
                    # Определяем символ для другого игрока
                    char = '@'

                    try:
                        curses.init_pair(1, curses.COLOR_GREEN, -1)
                        color_pair = curses.color_pair(1)
                    except Exception:
                        color_pair = 0

                    try:
                        stdscr.addch(other_screen_y, other_screen_x, char, color_pair)

                        # Подписываем имя игрока (если есть место)
                        if 'name' in other_player and other_screen_y + 1 < height:
                            name = other_player['name'][:10]
                            if other_screen_x + len(name) < width:
                                stdscr.addstr(
                                    other_screen_y + 1,
                                    other_screen_x - len(name) // 2 + 1,
                                    f'{name}',
                                )

                    except curses.error:
                        pass

        stdscr.refresh()

    def start_websocket_thread(self):
        """Запуск WebSocket в отдельном потоке"""

        def run_ws():
            asyncio.new_event_loop().run_until_complete(self.websocket_listener())

        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()

    def run(self):
        """Запуск клиента"""
        self.start_websocket_thread()

        def main(stdscr):
            curses.curs_set(0)
            stdscr.nodelay(1)
            stdscr.timeout(150)  # Таймаут для getch (мс)
            curses.start_color()
            curses.use_default_colors()

            frame = 0

            while True:
                # Обрабатываем сообщения от сервера
                self.process_server_messages()
                frame += 1

                # Обработка ввода
                key = stdscr.getch()
                if key != -1:
                    self.handle_input(key)

                # Рендеринг
                self.render(stdscr, frame)
                self.render_chat(stdscr)

        curses.wrapper(main)

    def handle_input(self, key):
        """Обработка пользовательского ввода"""
        if key in [ord('q'), ord('Q')]:
            exit()
        elif key in [ord('w'), ord('W'), curses.KEY_UP]:
            self.send_move(0, -1)
        elif key in [ord('s'), ord('S'), curses.KEY_DOWN]:
            self.send_move(0, 1)
        elif key in [ord('a'), ord('A'), curses.KEY_LEFT]:
            self.send_move(-1, 0)
        elif key in [ord('d'), ord('D'), curses.KEY_RIGHT]:
            self.send_move(1, 0)
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
            self.chat_field.edit()


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-s')
    # args = parser.parse_args()

    SERVER_IP = '178.72.129.84'

    login_form = LoginForm()
    token = login_form.run()

    gameClient = GameClient(
        SERVER_IP,
        token,
    )

    gameClient.run()


# def draw_title(stdscr: curses.window, text: str):
#     _, width = stdscr.getmaxyx()
#     border_wing = f'{"═" * (width // 2 - len(text) * 2)}'
#     title_win = curses.newwin(1, width, 0, 0)
#     title_win.clear()
#     title_win.addstr(0, 0, f'╒{border_wing} {text} {border_wing}╕')
#     title_win.refresh()
#
#
# def main(stdscr: curses.window):
#     stdscr.addstr('keka')
#     stdscr.refresh()
#
#     draw_title(stdscr, 'axui')
#
#     class player:
#         x: int = 10
#         y: int = 10
#
#     world_window = curses.newwin(30, 60, 2, 2)
#     world_window.addstr(player.x, player.y, '@')
#
#     stdscr.nodelay(True)
#     curses.curs_set(0)
#
#     rectangle(stdscr, 2, 65, 29, 85)
#     rectangle(stdscr, 30, 65, 32, 85)
#     chat_text_window = curses.newwin(1, 19, 31, 66)
#     box = Textbox(chat_text_window)
#     stdscr.refresh()
#
#     world_window.border(
#         curses.ACS_VLINE,
#         curses.ACS_VLINE,
#         curses.ACS_HLINE,
#         curses.ACS_HLINE,
#         curses.ACS_ULCORNER,
#         curses.ACS_URCORNER,
#         curses.ACS_LLCORNER,
#         curses.ACS_LRCORNER,
#     )
#     world_window.refresh()
#     frame = 0
#     while True:
#         frame += 1
#         curses.napms(10)
#         stdscr.addstr(1, 1, f'frame: {frame}')
#         try:
#             key = stdscr.getkey()
#         except:
#             continue
#         match key:
#             case 'q':
#                 exit()
#             case 'KEY_LEFT' | 'a':
#                 player.x -= 1
#             case 'KEY_RIGHT' | 'd':
#                 player.x += 1
#             case 'KEY_UP' | 'w':
#                 player.y -= 1
#             case 'KEY_DOWN' | 's':
#                 player.y += 1
#             case 'KEY_ENTER' | '\n':
#                 box.edit()
#                 _text = box.gather()
#                 world_window.refresh()
#
#         world_window.clear()
#         world_window.border(
#             curses.ACS_VLINE,
#             curses.ACS_VLINE,
#             curses.ACS_HLINE,
#             curses.ACS_HLINE,
#             curses.ACS_ULCORNER,
#             curses.ACS_URCORNER,
#             curses.ACS_LLCORNER,
#             curses.ACS_LRCORNER,
#         )
#         world_window.addstr(2, 2, f'Key: {key}'.ljust(20))
#         world_window.addstr(player.y, player.x, '@')
#         world_window.refresh()
