from fastapi import APIRouter, WebSocket

from src.api.dependencies import UserDep
from src.api.rest.auth import DbDep
from src.engine.GameProtocol import GameProtocol
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

        for player in gameSessionsManager.players.items():
            print(player[1].id)
            print(player[1].name)
            print(player[1].position)

            init_player_data = f'player_init:{player[1].id}:{player[1].name}:{player[1].position["x"]}:{player[1].position["y"]}'

            await websocket.send_bytes(init_player_data.encode('utf-8'))

        while True:
            data = await websocket.receive_text()
            if data:
                print(f'Recieved data: {data}')
    except Exception as ex:
        print(ex)
