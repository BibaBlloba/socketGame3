from fastapi import APIRouter, WebSocket

from src.api.dependencies import UserDep
from src.api.rest.auth import DbDep
from src.engine.GameProtocol import GameProtocol
from src.engine.GameSessionManager import gameSessionsManager

router = APIRouter(prefix='/game', tags=['ws'])


@router.websocket('/ws')
async def ws(db: DbDep, websocket: WebSocket, user: UserDep):
    await websocket.accept()
    await websocket.send_json(user)

    user_data = await db.users.get_uesr_with_hashedPwd(id=user['user_id'])

    gameSessionsManager.add_player(
        websocket, user['user_id'], user_data.name, user_data.x, user_data.y
    )

    for player in gameSessionsManager.players.items():
        print(player[1].id)
        print(player[1].name)
        print(player[1].position)

        await websocket.send_bytes(GameProtocol.pack_player_join(player[1].id))

    while True:
        data = await websocket.receive_text()
        if data:
            print(f'Recieved data: {data}')
