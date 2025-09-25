from typing import Dict

from fastapi import WebSocket


class PlayerSession:
    def __init__(
        self, websocket: WebSocket, id: int, name: str, x: int, y: int
    ) -> None:
        self.websocket = websocket
        self.id = id
        self.name = name
        if x is None:
            x = 0
        if y is None:
            y = 0
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
        self.players: Dict[str, PlayerSession] = {}

    def add_player(self, websocket: WebSocket, id: int, name: str, x: int, y: int):
        self.players[name] = PlayerSession(websocket, id, name, x, y)

    async def broadcast(self, message: str):
        for player in self.players.items():
            await player.send_message(message)


gameSessionsManager = GameSessionsManager()
