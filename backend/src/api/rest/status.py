from fastapi import APIRouter

router = APIRouter(prefix='/status', tags=['Status'])


@router.get('')
async def get_status():
    return {'status': 'ok'}
