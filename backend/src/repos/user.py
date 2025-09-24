from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import insert, select, update
from sqlalchemy.exc import NoResultFound

from models.user import UsersOrm
from src.repos.base import BaseRepository


class UserRepository(BaseRepository):
    model = UsersOrm

    async def get_uesr_with_hashedPwd(self, name):
        query = select(self.model).filter_by(name=name)
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def add(self, data: BaseModel):
        add_data_stmt = (
            insert(self.model).values(**data.model_dump()).returning(self.model)
        )
        try:
            result = await self.session.execute(add_data_stmt)
        except Exception:
            raise HTTPException(409, detail='User already exists')
        model = result.scalars().one()
        return model

    async def edit(
        self,
        data: BaseModel,
        exclude_unset: bool = False,
        **filter_by,
    ) -> None:
        update_stmt = (
            update(self.model)
            .filter_by(**filter_by)
            .values(data.model_dump(exclude_unset=exclude_unset))
            .returning(self.model)
        )
        try:
            result = await self.session.execute(update_stmt)
            model = result.scalars().one()
        except NoResultFound:
            raise HTTPException(404, 'Пользователь не найден')
        return model
