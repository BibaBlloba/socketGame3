from sqlalchemy import delete
from str.database import Base


class BaseRepository:
    model = Base

    def __init__(self, session):
        self.session = session

    async def delete(self, **filter_by) -> None:
        delete_stmt = delete(self.model).filter_by(**filter_by)
        result = await self.session.execute(delete_stmt)
        return result
