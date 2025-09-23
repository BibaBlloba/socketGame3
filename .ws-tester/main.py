# client/protocol.py
import asyncio
import struct
import time
from dataclasses import dataclass
from enum import IntEnum

import websockets


class MessageType(IntEnum):
    PLAYER_UPDATE = 1
    PLAYER_JOIN = 2
    PLAYER_LEAVE = 3
    CHAT_MESSAGE = 4
    WORLD_STATE = 5


@dataclass
class PlayerUpdate:
    player_name: str
    x: float
    y: float


@dataclass
class ChatMessage:
    player_name: str
    message: str


class ClientProtocol:
    """Клиентская реализация протокола (симметричная серверной)"""

    @staticmethod
    def pack_player_update(update: PlayerUpdate) -> bytes:
        """Упаковка обновления позиции игрока (такая же как на сервере)"""
        data = struct.pack(
            "!B I f f f f f",
            MessageType.PLAYER_UPDATE,
            update.player_name,  # TODO: тут
            update.x,
            update.y,
            update.z,
            update.rotation,
            update.timestamp,
        )
        return data

    @staticmethod
    def unpack_player_update(data: bytes) -> PlayerUpdate:
        """Распаковка обновления позиции игрока"""
        msg_type, player_id, x, y, z, rotation, timestamp = struct.unpack(
            "!B I f f f f f", data
        )
        return PlayerUpdate(player_id, x, y, z, rotation, timestamp)

    @staticmethod
    def pack_chat_message(chat: ChatMessage) -> bytes:
        """Упаковка чат-сообщения"""
        message_bytes = chat.message.encode("utf-8")
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
        msg_type, player_id, msg_length = struct.unpack("!B I I", data[:9])
        full_format = f"!B I I {msg_length}s f"
        msg_type, player_id, msg_length, message_bytes, timestamp = struct.unpack(
            full_format, data
        )
        return ChatMessage(player_id, message_bytes.decode("utf-8"), timestamp)

    @staticmethod
    def unpack_player_join(data: bytes) -> int:
        """Распаковка сообщения о подключении игрока"""
        msg_type, player_id = struct.unpack("!B I", data)
        return player_id

    @staticmethod
    def unpack_player_leave(data: bytes) -> int:
        """Распаковка сообщения об отключении игрока"""
        msg_type, player_id = struct.unpack("!B I", data)
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


async def main():
    print("connecting...")
    webs = await websockets.connect("ws://localhost:8000/game/ws")
    print("Connected\n")

    message = ChatMessage("akeka", "hello xyuzzz!")

    while True:
        time.sleep(2)


asyncio.run(main())
