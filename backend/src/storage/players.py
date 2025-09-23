from typing import Dict

from fastapi import WebSocket


class PlayerSession:
    def __init__(self, websocket: WebSocket, name: int, x: int, y: int) -> None:
        self.websocket = websocket
        self.name = name
        self.position = {'x': x, 'y': y}

    def update_position(self, x: int, y: int):
        self.position = {'x': x, 'y': y}

    async def send_message(self, message: str):
        try:
            await self.websocket.send_text(message)
        except Exception as ex:
            print(f'error: {ex}')


class GameSessionsManager:
    def __init__(self) -> None:
        self.players = Dict[str, PlayerSession] = {}

    def add_player(self, websocket: WebSocket, name, x: int, y: int):
        self.players[name] = PlayerSession(websocket, name, x, y)

    async def broadcast(self, message: str):
        for player in self.players.items():
            await player.send_message(message)
