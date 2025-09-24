from fastapi import APIRouter, Body, HTTPException

from services.auth import AuthService
from src.api.dependencies import DbDep
from src.schemas.user import UserAdd, UserAddRequest

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post('/register')
async def register_user(db: DbDep, data: UserAddRequest = Body()):
    if data.name == '' or data.password == '':
        raise HTTPException(401)

    hashed_password = AuthService().hash_password(data.password)
    hashed_user_data = UserAdd(name=data.name, hashed_password=hashed_password)
    result = await db.users.add(hashed_user_data)
    await db.commit()
    return result
