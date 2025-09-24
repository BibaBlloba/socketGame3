from src.utils.db_manager import DbManager


class BaseService:
    def __init__(self, db: DbManager | None = None) -> None:
        self.db = db
