import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


@dataclass
class MessageType(IntEnum):
    PLAYER_UPDATE = 1
    PLAYER_JOIN = 2
    PLAYER_LEAVE = 3
    CHAT_MESSAGE = 4
    WORLD_STATE = 5


@dataclass
class PlayerUpdate:
    player_name: str
    x: int
    y: int


@dataclass
class ChatMessage:
    player_name: str
    message: str


class GameProtocol:
    FORMATS = {
        MessageType.PLAYER_UPDATE: '20siii',
        MessageType.PLAYER_JOIN: '!20s',
        MessageType.PLAYER_LEAVE: '!20s',
    }

    @staticmethod
    def pack_chat_message(chat: ChatMessage) -> bytes:
        """Упаковка чат-сообщения"""
        message_bytes = chat.message.encode('utf-8')
        # Байт типа + player_id + длина сообщения + сообщение
        data = struct.pack(
            f'!B 20s 20s {len(message_bytes)}s',
            MessageType.CHAT_MESSAGE,
            chat.player_name,
            len(message_bytes),
            message_bytes,
        )
        return data

    @staticmethod
    def pack_player_join(player_name: int) -> bytes:
        """Упаковка сообщения о подключении игрока"""
        return struct.pack('!B 20s', MessageType.PLAYER_JOIN, player_name)

    @staticmethod
    def unpack_player_join(data: bytes) -> int:
        """Распаковка сообщения о подключении игрока"""
        msg_type, player_name = struct.unpack('!B 20s', data)
        return player_name

    @staticmethod
    def pack_player_leave(player_name: int) -> bytes:
        """Упаковка сообщения об отключении игрока"""
        return struct.pack('!B 20s', MessageType.PLAYER_LEAVE, player_name)

    @staticmethod
    def unpack_player_leave(data: bytes) -> int:
        """Распаковка сообщения об отключении игрока"""
        msg_type, player_name = struct.unpack('!B 20s', data)
        return player_name

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
            print(f'Ошибка распаковки сообщения типа {msg_type}: {e}')
            return None
