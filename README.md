План:

- [ ] Написать базовый FastAPI сервер без авторизации для вебсоветов
  - [x] FastAPI сервер
  - [x] Хранение состояния игроков
  - [x] Изменение состояний
  - [ ] GameProtocol для запаковки и распаковки данных в байтах
  - [ ] Карта мира
  - [ ] Чат
- [ ] Сделать главное меню для смены ника и выбора сервера/режима игры
- [ ] Сделать подключение клиента по нику, без пароля
- [ ] Сделать авторизацию
  - [ ] на сервере
  - [ ] на клиенте



### GameProtocol

- Server
```python
# server/protocol.py
import struct
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Any

class MessageType(IntEnum):
    PLAYER_UPDATE = 1
    PLAYER_JOIN = 2
    PLAYER_LEAVE = 3
    CHAT_MESSAGE = 4
    WORLD_STATE = 5

@dataclass
class PlayerUpdate:
    player_id: int
    x: float
    y: float
    z: float
    rotation: float  # Поворот игрока
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class ChatMessage:
    player_id: int
    message: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class GameProtocol:
    # Форматы struct для разных типов сообщений
    FORMATS = {
        MessageType.PLAYER_UPDATE: '!Ifffff',  # player_id, x, y, z, rotation, timestamp
        MessageType.PLAYER_JOIN: '!I',         # player_id
        MessageType.PLAYER_LEAVE: '!I',        # player_id
    }
    
    @staticmethod
    def pack_player_update(update: PlayerUpdate) -> bytes:
        """Упаковка обновления позиции игрока"""
        # Упаковка основных данных
        data = struct.pack(
            '!B I f f f f f',  # B - тип сообщения, I - player_id, 5xf - координаты
            MessageType.PLAYER_UPDATE,
            update.player_id,
            update.x,
            update.y,
            update.z,
            update.rotation,
            update.timestamp
        )
        return data
    
    @staticmethod
    def unpack_player_update(data: bytes) -> PlayerUpdate:
        """Распаковка обновления позиции игрока"""
        msg_type, player_id, x, y, z, rotation, timestamp = struct.unpack('!B I f f f f f', data)
        return PlayerUpdate(player_id, x, y, z, rotation, timestamp)
    
    @staticmethod
    def pack_chat_message(chat: ChatMessage) -> bytes:
        """Упаковка чат-сообщения"""
        message_bytes = chat.message.encode('utf-8')
        # Байт типа + player_id + длина сообщения + сообщение + timestamp
        data = struct.pack(
            f'!B I I {len(message_bytes)}s f',
            MessageType.CHAT_MESSAGE,
            chat.player_id,
            len(message_bytes),
            message_bytes,
            chat.timestamp
        )
        return data
    
    @staticmethod
    def unpack_chat_message(data: bytes) -> ChatMessage:
        """Распаковка чат-сообщения"""
        # Сначала читаем заголовок чтобы узнать длину сообщения
        msg_type, player_id, msg_length = struct.unpack('!B I I', data[:9])
        # Затем читаем полное сообщение
        full_format = f'!B I I {msg_length}s f'
        msg_type, player_id, msg_length, message_bytes, timestamp = struct.unpack(full_format, data)
        return ChatMessage(player_id, message_bytes.decode('utf-8'), timestamp)
    
    @staticmethod
    def pack_player_join(player_id: int) -> bytes:
        """Упаковка сообщения о подключении игрока"""
        return struct.pack('!B I', MessageType.PLAYER_JOIN, player_id)
    
    @staticmethod
    def unpack_player_join(data: bytes) -> int:
        """Распаковка сообщения о подключении игрока"""
        msg_type, player_id = struct.unpack('!B I', data)
        return player_id
    
    @staticmethod
    def pack_player_leave(player_id: int) -> bytes:
        """Упаковка сообщения об отключении игрока"""
        return struct.pack('!B I', MessageType.PLAYER_LEAVE, player_id)
    
    @staticmethod
    def unpack_player_leave(data: bytes) -> int:
        """Распаковка сообщения об отключении игрока"""
        msg_type, player_id = struct.unpack('!B I', data)
        return player_id

    @staticmethod
    def unpack_message(data: bytes) -> Any:
        """Универсальная распаковка по типу сообщения"""
        if not data:
            return None
            
        msg_type = data[0]  # Первый байт - тип сообщения
        
        try:
            if msg_type == MessageType.PLAYER_UPDATE:
                return GameProtocol.unpack_player_update(data)
            elif msg_type == MessageType.CHAT_MESSAGE:
                return GameProtocol.unpack_chat_message(data)
            elif msg_type == MessageType.PLAYER_JOIN:
                return GameProtocol.unpack_player_join(data)
            elif msg_type == MessageType.PLAYER_LEAVE:
                return GameProtocol.unpack_player_leave(data)
        except Exception as e:
            print(f"Ошибка распаковки сообщения типа {msg_type}: {e}")
            return None
```

```python
# server/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from protocol import GameProtocol, PlayerUpdate, ChatMessage

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.player_positions: Dict[int, PlayerUpdate] = {}
    
    async def connect(self, websocket: WebSocket, player_id: int):
        await websocket.accept()
        self.active_connections[player_id] = websocket
        # Уведомляем всех о новом игроке
        join_msg = GameProtocol.pack_player_join(player_id)
        await self.broadcast(join_msg, exclude_player=player_id)
    
    def disconnect(self, player_id: int):
        if player_id in self.active_connections:
            del self.active_connections[player_id]
        if player_id in self.player_positions:
            del self.player_positions[player_id]
    
    async def broadcast(self, message: bytes, exclude_player: int = None):
        disconnected = []
        for pid, websocket in self.active_connections.items():
            if pid != exclude_player:
                try:
                    await websocket.send_bytes(message)
                except:
                    disconnected.append(pid)
        
        for pid in disconnected:
            self.disconnect(pid)

manager = ConnectionManager()

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: int):
    await manager.connect(websocket, player_id)
    
    try:
        while True:
            # Ожидаем binary данные от клиента
            data = await websocket.receive_bytes()
            
            # Распаковываем сообщение
            message = GameProtocol.unpack_message(data)
            
            if isinstance(message, PlayerUpdate):
                # Обновляем позицию игрока
                manager.player_positions[player_id] = message
                
                # Рассылаем обновление другим игрокам
                update_msg = GameProtocol.pack_player_update(message)
                await manager.broadcast(update_msg, exclude_player=player_id)
                
            elif isinstance(message, ChatMessage):
                # Рассылаем сообщение чата всем
                chat_msg = GameProtocol.pack_chat_message(message)
                await manager.broadcast(chat_msg)
                
    except WebSocketDisconnect:
        manager.disconnect(player_id)
        # Уведомляем об отключении игрока
        leave_msg = GameProtocol.pack_player_leave(player_id)
        await manager.broadcast(leave_msg)

# Отправка периодических обновлений мира
async def send_world_updates():
    while True:
        await asyncio.sleep(0.1)  # 10 раз в секунду
        # Здесь можно рассылать обновления состояния мира

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(send_world_updates())
```


- Client
```python
# client/protocol.py
import struct
import time
from dataclasses import dataclass
from enum import IntEnum

class MessageType(IntEnum):
    PLAYER_UPDATE = 1
    PLAYER_JOIN = 2
    PLAYER_LEAVE = 3
    CHAT_MESSAGE = 4
    WORLD_STATE = 5

@dataclass
class PlayerUpdate:
    player_id: int
    x: float
    y: float
    z: float
    rotation: float
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class ChatMessage:
    player_id: int
    message: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class ClientProtocol:
    """Клиентская реализация протокола (симметричная серверной)"""
    
    @staticmethod
    def pack_player_update(update: PlayerUpdate) -> bytes:
        """Упаковка обновления позиции игрока (такая же как на сервере)"""
        data = struct.pack(
            '!B I f f f f f',
            MessageType.PLAYER_UPDATE,
            update.player_id,
            update.x,
            update.y,
            update.z,
            update.rotation,
            update.timestamp
        )
        return data
    
    @staticmethod
    def unpack_player_update(data: bytes) -> PlayerUpdate:
        """Распаковка обновления позиции игрока"""
        msg_type, player_id, x, y, z, rotation, timestamp = struct.unpack('!B I f f f f f', data)
        return PlayerUpdate(player_id, x, y, z, rotation, timestamp)
    
    @staticmethod
    def pack_chat_message(chat: ChatMessage) -> bytes:
        """Упаковка чат-сообщения"""
        message_bytes = chat.message.encode('utf-8')
        data = struct.pack(
            f'!B I I {len(message_bytes)}s f',
            MessageType.CHAT_MESSAGE,
            chat.player_id,
            len(message_bytes),
            message_bytes,
            chat.timestamp
        )
        return data
    
    @staticmethod
    def unpack_chat_message(data: bytes) -> ChatMessage:
        """Распаковка чат-сообщения"""
        msg_type, player_id, msg_length = struct.unpack('!B I I', data[:9])
        full_format = f'!B I I {msg_length}s f'
        msg_type, player_id, msg_length, message_bytes, timestamp = struct.unpack(full_format, data)
        return ChatMessage(player_id, message_bytes.decode('utf-8'), timestamp)
    
    @staticmethod
    def unpack_player_join(data: bytes) -> int:
        """Распаковка сообщения о подключении игрока"""
        msg_type, player_id = struct.unpack('!B I', data)
        return player_id
    
    @staticmethod
    def unpack_player_leave(data: bytes) -> int:
        """Распаковка сообщения об отключении игрока"""
        msg_type, player_id = struct.unpack('!B I', data)
        return player_id
    
    @staticmethod
    def unpack_message(data: bytes):
        """Универсальная распаковка по типу сообщения"""
        if not data:
            return None
            
        msg_type = data[0]
        
        try:
            if msg_type == MessageType.PLAYER_UPDATE:
                return ClientProtocol.unpack_player_update(data)
            elif msg_type == MessageType.CHAT_MESSAGE:
                return ClientProtocol.unpack_chat_message(data)
            elif msg_type == MessageType.PLAYER_JOIN:
                return ClientProtocol.unpack_player_join(data)
            elif msg_type == MessageType.PLAYER_LEAVE:
                return ClientProtocol.unpack_player_leave(data)
        except Exception as e:
            print(f"Ошибка распаковки: {e}")
            return None
```

```python
# client/game_client.py
import asyncio
import websockets
from protocol import ClientProtocol, PlayerUpdate, ChatMessage

class GameClient:
    def __init__(self, server_url: str, player_id: int):
        self.server_url = server_url
        self.player_id = player_id
        self.websocket = None
        self.players = {}  # Состояния других игроков
        
    async def connect(self):
        """Подключение к серверу"""
        self.websocket = await websockets.connect(
            f"{self.server_url}/ws/{self.player_id}"
        )
        print(f"Подключен к серверу как игрок {self.player_id}")
        
    async def send_player_update(self, x: float, y: float, z: float, rotation: float):
        """Отправка обновления позиции"""
        if self.websocket:
            update = PlayerUpdate(self.player_id, x, y, z, rotation)
            data = ClientProtocol.pack_player_update(update)
            await self.websocket.send(data)
    
    async def send_chat_message(self, message: str):
        """Отправка сообщения в чат"""
        if self.websocket:
            chat = ChatMessage(self.player_id, message)
            data = ClientProtocol.pack_chat_message(chat)
            await self.websocket.send(data)
    
    async def listen_server(self):
        """Прослушивание сообщений от сервера"""
        try:
            async for message in self.websocket:
                # Обрабатываем binary сообщение
                decoded = ClientProtocol.unpack_message(message)
                
                if isinstance(decoded, PlayerUpdate):
                    self.handle_player_update(decoded)
                elif isinstance(decoded, ChatMessage):
                    self.handle_chat_message(decoded)
                elif isinstance(decoded, int):  # JOIN/LEAVE
                    if message[0] == 2:  # PLAYER_JOIN
                        self.handle_player_join(decoded)
                    else:  # PLAYER_LEAVE
                        self.handle_player_leave(decoded)
                        
        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером разорвано")
    
    def handle_player_update(self, update: PlayerUpdate):
        """Обработка обновления позиции игрока"""
        if update.player_id != self.player_id:  # Не себя
            self.players[update.player_id] = update
            print(f"Игрок {update.player_id} переместился: {update.x}, {update.y}")
    
    def handle_chat_message(self, chat: ChatMessage):
        """Обработка сообщения чата"""
        print(f"Игрок {chat.player_id}: {chat.message}")
    
    def handle_player_join(self, player_id: int):
        """Обработка подключения нового игрока"""
        print(f"Игрок {player_id} присоединился к игре")
        self.players[player_id] = None
    
    def handle_player_leave(self, player_id: int):
        """Обработка отключения игрока"""
        print(f"Игрок {player_id} покинул игру")
        if player_id in self.players:
            del self.players[player_id]
    
    async def run(self):
        """Основной цикл клиента"""
        await self.connect()
        
        # Запускаем прослушивание в фоне
        listener_task = asyncio.create_task(self.listen_server())
        
        try:
            # Пример игрового цикла
            import random
            while True:
                # Симуляция движения игрока
                x = random.uniform(0, 100)
                y = random.uniform(0, 100)
                z = 0
                rotation = random.uniform(0, 360)
                
                await self.send_player_update(x, y, z, rotation)
                await asyncio.sleep(0.1)  # 10 обновлений в секунду
                
        except KeyboardInterrupt:
            print("Выход из игры...")
        finally:
            listener_task.cancel()
            if self.websocket:
                await self.websocket.close()

# Запуск клиента
async def main():
    client = GameClient("ws://localhost:8000", player_id=123)
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
```
