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

        if user_data.x is None:
            user_data.x = 0
        if user_data.y is None:
            user_data.y = 0

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

        for (
            existing_player_name,
            existing_player,
        ) in gameSessionsManager.players.items():
            if existing_player.id == user['user_id']:
                continue

            existing_player_data = PlayerJoin(
                existing_player.id,
                existing_player.name,
                existing_player.position['x'],
                existing_player.position['y'],
            )
            await websocket.send_bytes(
                GameProtocol.pack_player_join(existing_player_data)
            )

        for _, player in gameSessionsManager.players.items():
            if player.id == user['user_id']:
                continue

            data = PlayerJoin(
                user['user_id'],
                user_data.name,
                user_data.x,
                user_data.y,
            )
            print(f'player join send: {user_data.name}')
            print(data)
            await player.websocket.send_bytes(GameProtocol.pack_player_join(data))

        while True:
            message = await websocket.receive_bytes()
            try:
                if message:
                    data = GameProtocol.unpack_message(message)

                    if data is None:
                        print('Не удалось распаковать сообщение')
                        return

                    print(f'{data=}')
                    print('name =', data.name)

                if isinstance(data, PlayerUpdate):
                    if data.name in gameSessionsManager.players:
                        gameSessionsManager.players[data.name].position['x'] = data.x
                        gameSessionsManager.players[data.name].position['y'] = data.y
                        print('player pos updated')

                        for _, player in gameSessionsManager.players.items():
                            if player.id == user['user_id']:
                                continue
                            await player.websocket.send_bytes(message)
                    else:
                        print(f'Игрок {data.name} не найден')
            except Exception as ex:
                print(f'ex 2: {ex}')

    except WebSocketDisconnect:
        print(f'{user_data.name} disconnected')
        message = GameProtocol.pack_player_leave(user['user_id'])
        del gameSessionsManager.players[user_data.name]

        for _, player in gameSessionsManager.players.items():
            await player.websocket.send_bytes(message)

    except Exception as ex:
        print('ex: ', ex)
