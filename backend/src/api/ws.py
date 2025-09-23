from fastapi import APIRouter, WebSocket

from engine.GameProtocol import GameProtocol

router = APIRouter(prefix='/game', tags=['ws'])


@router.websocket('/ws')
async def ws(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_bytes()
    message = GameProtocol.unpack_message(data)
    print(f'{data=}')
    print(f'{message=}')

    while True:
        data = await websocket.receive_text()
        if data:
            print(f'Recieved data: {data}')
