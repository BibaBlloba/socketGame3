from typing import Annotated

import jwt
from fastapi import Depends, Query, WebSocket, WebSocketException, status

from services.auth import AuthService
from src.database import async_session_maker
from utils.db_manager import DbManager


async def get_current_user(websocket: WebSocket, token: str = Query()):
    try:
        data = AuthService().decode_token(token)
    except jwt.exceptions.DecodeError:
        await websocket.close()
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, detail='Invalid authentication token'
        )
    return data  # FIX: Пока не понятно, что он возвращает


UserDep = Annotated[dict, Depends(get_current_user)]


async def get_db():
    async with DbManager(session_factory=async_session_maker) as db:
        yield db


DbDep = Annotated[DbManager, Depends(get_db)]
