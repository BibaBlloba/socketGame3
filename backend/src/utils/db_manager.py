from src.repos.user import UserRepository


class DbManager:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        """Репозитории"""
        self.users = UserRepository(self.session)

        return self

    async def __aexit__(self, *args):  # *args для обработки ошибок
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
