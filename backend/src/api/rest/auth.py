from fastapi import APIRouter, Body, HTTPException

from services.auth import AuthService
from src.api.dependencies import DbDep
from src.schemas.user import UserAdd, UserAddRequest, UserLogin

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


@router.post('/login')
async def login_user(db: DbDep, data: UserLogin):
    user = await db.users.get_uesr_with_hashedPwd(name=data.name)
    if not user or not AuthService().verify_password(
        data.password, user.hashed_password
    ):
        raise HTTPException(status_code=401)
    access_token = AuthService().create_access_token({'user_id': user.id})
    return {'access_token': access_token}
