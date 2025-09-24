from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class UsersOrm(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True)
    x: Mapped[int] = mapped_column(nullable=True)
    y: Mapped[int] = mapped_column(nullable=True)

    hashed_password: Mapped[str] = mapped_column(String(100))
