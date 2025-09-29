from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.dependencies import UserDep
from src.api.rest.auth import DbDep
from src.engine.GameProtocol import (GameProtocol, PlayerInit, PlayerJoin,
                                     PlayerUpdate)
from src.engine.GameSessionManager import gameSessionsManager

router = APIRouter(prefix='/game', tags=['ws'])


@router.websocket('/ws')
async def ws(db: DbDep, websocket: WebSocket, user: UserDep):
    try:
        await websocket.accept()

        user_data = await db.users.get_uesr_with_hashedPwd(id=user['user_id'])

        gameSessionsManager.add_player(
            websocket, user['user_id'], user_data.name, user_data.x, user_data.y
        )

        player = gameSessionsManager.players[user_data.name]
        init_player_data = PlayerInit(
            player.id,
            player.name,
            player.position['x'],
            player.position['y'],
        )
        data = GameProtocol.pack_player_init(init_player_data)
        await websocket.send_bytes(data)

        for _, player in gameSessionsManager.players.items():
            if player.id == user['user_id']:
                continue

            data = PlayerJoin(
                player.id,
                player.name,
                player.position['x'],
                player.position['y'],
            )
            print(f'player join send: {user_data.name}')
            print(data)
            await player.websocket.send_bytes(GameProtocol.pack_player_join(data))

        while True:
            message = await websocket.receive_bytes()
            if message:
                data = GameProtocol.unpack_message(message)
                print(data)

                if isinstance(data, PlayerUpdate):
                    gameSessionsManager.players[data.name]

    except WebSocketDisconnect:
        print(f'{user_data.name} disconnected')
        del gameSessionsManager.players[user_data.name]
    except Exception as ex:
        print('ex: ', ex)
