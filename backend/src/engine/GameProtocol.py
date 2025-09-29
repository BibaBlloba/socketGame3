import struct
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class MessageType(IntEnum):
    PLAYER_UPDATE = 1
    PLAYER_JOIN = 2
    PLAYER_LEAVE = 3
    CHAT_MESSAGE = 4
    WORLD_STATE = 5
    PLAYER_INIT = 6


@dataclass
class PlayerInit:
    player_id: int
    name: str
    x: int
    y: int


@dataclass
class PlayerJoin:
    player_id: int
    name: str
    x: int
    y: int


@dataclass
class PlayerUpdate:
    player_id: int
    name: str
    x: int
    y: int


@dataclass
class ChatMessage:
    player_id: int
    message: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class GameProtocol:
    @staticmethod
    def pack_player_init(init: PlayerInit):
        """Упаковка инициализации игрока"""
        data = struct.pack(
            '!BI20sii',
            MessageType.PLAYER_INIT,
            init.player_id,
            init.name.encode('utf-8'),
            init.x,
            init.y,
        )
        return data

    @staticmethod
    def unpack_player_init(data: bytes):
        _, player_id, name, x, y = struct.unpack('!BI20sii', data)
        return PlayerInit(player_id, name, x, y)

    @staticmethod
    def pack_player_update(update: PlayerUpdate) -> bytes:
        """Упаковка обновления позиции игрока"""
        # Упаковка основных данных
        data = struct.pack(
            '!BI20sii',
            MessageType.PLAYER_UPDATE,
            update.player_id,
            update.name.encode('utf-8'),
            update.x,
            update.y,
        )
        return data

    @staticmethod
    def unpack_player_update(data: bytes) -> PlayerUpdate:
        """Распаковка обновления позиции игрока"""
        msg_type, player_id, name_bytes, x, y = struct.unpack('!BI20sii', data)
        name = name_bytes.decode('utf-8').rstrip('\x00')
        return PlayerUpdate(player_id, name, x, y)

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
            chat.timestamp,
        )
        return data

    @staticmethod
    def unpack_chat_message(data: bytes) -> ChatMessage:
        """Распаковка чат-сообщения"""
        # Сначала читаем заголовок чтобы узнать длину сообщения
        msg_type, player_id, msg_length = struct.unpack('!B I I', data[:9])
        # Затем читаем полное сообщение
        full_format = f'!B I I {msg_length}s f'
        msg_type, player_id, msg_length, message_bytes, timestamp = struct.unpack(
            full_format, data
        )
        return ChatMessage(player_id, message_bytes.decode('utf-8'), timestamp)

    @staticmethod
    def pack_player_join(join_data: PlayerJoin) -> bytes:
        """Упаковка сообщения о подключении игрока"""
        data = struct.pack(
            '!B I 20s i i',
            MessageType.PLAYER_JOIN,
            join_data.player_id,
            join_data.name.encode('utf-8'),
            join_data.x,
            join_data.y,
        )
        return data

    @staticmethod
    def unpack_player_join(data: bytes) -> int:
        """Распаковка сообщения о подключении игрока"""
        _, player_id, name, x, y = struct.unpack('!B I 20s i i', data)
        return PlayerJoin(player_id, name, x, y)

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
            elif msg_type == MessageType.PLAYER_INIT:
                return GameProtocol.unpack_player_init(data)
        except Exception as e:
            print(f'Ошибка распаковки сообщения типа {msg_type}: {e}')
            return None
