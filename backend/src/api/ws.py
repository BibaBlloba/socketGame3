from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.dependencies import UserDep
from src.api.rest.auth import DbDep
from src.engine.GameProtocol import GameProtocol, PlayerInit
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

        while True:
            data = await websocket.receive_bytes()
            if data:
                print(f'Recieved data: {data}')
    except WebSocketDisconnect:
        del gameSessionsManager.players[user_data.name]
    except Exception as ex:
        print('ex: ', ex)
