from fastapi import APIRouter, WebSocket

router = APIRouter(prefix='/game', tags=['ws'])


@router.websocket('/ws')
async def ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        if data:
            print(f'Recieved data: {data}')
