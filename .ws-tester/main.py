# client/protocol.py
import asyncio
import struct
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import websockets


class MessageType(IntEnum):
    PLAYER_UPDATE = 1
    PLAYER_JOIN = 2
    PLAYER_LEAVE = 3
    CHAT_MESSAGE = 4
    WORLD_STATE = 5


@dataclass
class PlayerUpdate:
    player_id: int
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
    FORMATS = {
        MessageType.PLAYER_UPDATE: "!Iii",  # player_id, x, y
        MessageType.PLAYER_JOIN: "!I",  # player_id
        MessageType.PLAYER_LEAVE: "!I",  # player_id
    }

    @staticmethod
    def pack_player_update(update: PlayerUpdate) -> bytes:
        """Упаковка обновления позиции игрока"""
        # Упаковка основных данных
        data = struct.pack(
            "!BIii",
            MessageType.PLAYER_UPDATE,
            update.player_id,
            update.x,
            update.y,
        )
        return data

    @staticmethod
    def unpack_player_update(data: bytes) -> PlayerUpdate:
        """Распаковка обновления позиции игрока"""
        msg_type, player_id, x, y = struct.unpack("!BIii", data)
        return PlayerUpdate(player_id, x, y)

    @staticmethod
    def pack_chat_message(chat: ChatMessage) -> bytes:
        """Упаковка чат-сообщения"""
        message_bytes = chat.message.encode("utf-8")
        # Байт типа + player_id + длина сообщения + сообщение + timestamp
        data = struct.pack(
            f"!B I I {len(message_bytes)}s f",
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
        msg_type, player_id, msg_length = struct.unpack("!B I I", data[:9])
        # Затем читаем полное сообщение
        full_format = f"!B I I {msg_length}s f"
        msg_type, player_id, msg_length, message_bytes, timestamp = struct.unpack(
            full_format, data
        )
        return ChatMessage(player_id, message_bytes.decode("utf-8"), timestamp)

    @staticmethod
    def pack_player_join(player_id: int) -> bytes:
        """Упаковка сообщения о подключении игрока"""
        return struct.pack("!B I", MessageType.PLAYER_JOIN, player_id)

    @staticmethod
    def unpack_player_join(data: bytes) -> int:
        """Распаковка сообщения о подключении игрока"""
        msg_type, player_id = struct.unpack("!B I", data)
        return player_id

    @staticmethod
    def pack_player_leave(player_id: int) -> bytes:
        """Упаковка сообщения об отключении игрока"""
        return struct.pack("!B I", MessageType.PLAYER_LEAVE, player_id)

    @staticmethod
    def unpack_player_leave(data: bytes) -> int:
        """Распаковка сообщения об отключении игрока"""
        msg_type, player_id = struct.unpack("!B I", data)
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


async def main():
    print("connecting...")
    webs = await websockets.connect(
        "ws://localhost:8000/game/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NTg3NDYxMjN9.SL1UXIAbqrg3AlrWgRhXkVheCRTrmNrcnqTUWWWTY5E"
    )
    print("Connected\n")

    while True:
        message: bytes = await webs.recv()

        if message:
            print(GameProtocol.unpack_message(message))


asyncio.run(main())
