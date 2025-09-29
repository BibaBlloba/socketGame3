import argparse
import asyncio
import curses
import threading
import time
from curses.textpad import Textbox, rectangle
from queue import Queue

import requests
import websockets

from engine.GameProtocol import GameProtocol, PlayerInit, PlayerUpdate


class GameClient:
    def __init__(self, server_url: str, token: str) -> None:
        self.player_id: int = None
        self.server_url = f'ws://{server_url}:8000/game/ws?token={token}'
        self.game_state = {
            'player': {'id': 0, 'name': None, 'x': 0, 'y': 0},
            'objects': {},
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

                # Запускаем задачу для отправки исходящих сообщений
                send_task = asyncio.create_task(self.outgoing_sender())

                message = await ws.recv()
                self.message_queue.put(message)

                try:
                    while True:
                        message = await ws.recv()
                        self.message_queue.put(message)
                finally:
                    send_task.cancel()
                    await send_task
        except Exception as e:
            print(f'WebSocket error: {e}')
            self.running = False

    async def outgoing_sender(self):
        """Отправка исходящих сообщений из очереди"""
        while self.running:
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
                continue  # Проверяем running условие
            except Exception as e:
                print(f'Send error: {e}')

    def process_server_messages(self):
        """Обработка сообщений от сервера (вызывается в основном потоке)"""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.handle_server_message(message)

    def handle_server_message(self, message: bytes):
        """Разбор сообщений от сервера"""
        data = GameProtocol.unpack_message(message)
        self.game_state['last_message'] = f'{self.game_state["chat"]=}'

        try:
            if isinstance(data, PlayerInit):
                self.add_chat_message('player_init')
                self.add_chat_message(f'{data}')
                _name = data.name.decode('utf-8').replace('\0', '')

                self.player_id = data.player_id
                self.game_state['player'] = {
                    'id': data.player_id,
                    'name': _name,
                    'x': data.x,
                    'y': data.y,
                }
        except Exception as e:
            raise e

        # try:
        #     if command == 'player_init':
        #         # player_init:id:name:x:y
        #         _, id, name, x, y = parts
        #         self.player_id = int(id)
        #         self.game_state['player'] = {
        #             'id': int(id),
        #             'name': name,
        #             'x': int(x),
        #             'y': int(y),
        #         }
        #
        #     elif command == 'player_move':
        #         # player_move:id:x:y
        #         _, id, x, y = parts
        #         if id in self.game_state['objects']:
        #             self.game_state['objects'][id]['x'] = int(x)
        #             self.game_state['objects'][id]['y'] = int(y)
        #
        #     elif command == 'obj_add':
        #         # obj_add:id:type:x:y
        #         (_, id, obj_type, x, y) = parts
        #         self.game_state['objects'][id] = {
        #             'id': id,
        #             'type': obj_type,
        #             'x': int(x),
        #             'y': int(y),
        #         }
        #
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
                PlayerUpdate(self.player_id, new_x, new_y)
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

        # Рисуем сообщения
        for i, msg in enumerate(self.game_state['chat'][-chat_height + 2 :]):
            chat_win.addstr(chat_height - 2 - i, 1, msg[: chat_width - 2])

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
