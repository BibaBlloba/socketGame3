import argparse
import asyncio
import curses
import threading
from queue import Queue

import requests
import websockets

from engine.GameProtocol import (GameProtocol, MessageType, PlayerInit,
                                 PlayerJoin, PlayerUpdate)


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
        }
        self.message_queue = Queue()
        self.outgoing_queue = Queue()
        self.websocket = None

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

        #     elif command == 'player_leave':
        #         # player_leave:id
        #         _, id = parts
        #         if id in self.game_state['objects']:
        #             del self.game_state['objects'][id]
        #
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
        chat_win.addstr(0, 2, ' XUI ')

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

    def render(self, stdscr: curses.window, frame):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        player = self.game_state['player']

        stdscr.addstr(0, 0, f'frame: {frame}')
        stdscr.addstr(0, 20, f'name: {self.game_state["player"]["name"]}')
        stdscr.addstr(1, 20, f'id: {self.player_id}')
        stdscr.addstr(0, 40, f'last_message: {self.game_state["last_message"]}')
        stdscr.addstr(1, 40, f'x: {self.game_state["player"]["x"]}')
        stdscr.addstr(2, 40, f'y: {self.game_state["player"]["y"]}')

        # Центрируем камеру на игроке
        camera_x = player['x'] - width // 2
        camera_y = player['y'] - height // 2

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
                                    other_screen_y + 1, other_screen_x, f'{name}'
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
            curses.curs_set(0)  # Скрываем курсор
            stdscr.nodelay(1)  # Неблокирующий ввод
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
        elif key in [ord('w'), ord('W')]:
            self.send_move(0, -1)
        elif key in [ord('s'), ord('S')]:
            self.send_move(0, 1)
        elif key in [ord('a'), ord('A')]:
            self.send_move(-1, 0)
        elif key in [ord('d'), ord('D')]:
            self.send_move(1, 0)


parser = argparse.ArgumentParser()
parser.add_argument('-u')
args = parser.parse_args()

token = requests.post(
    'http://localhost:8000/auth/login', json={'name': args.u, 'password': 'string'}
).json()['access_token']

gameClient = GameClient(
    'localhost',
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
