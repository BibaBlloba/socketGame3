from pydantic import BaseModel, ConfigDict


class UserAddRequest(BaseModel):
    name: str
    password: str


class UserAdd(BaseModel):
    name: str
    hashed_password: str


class UserLogin(BaseModel):
    name: str
    password: str


class User(BaseModel):
    id: int
    name: str
    x: int
    y: int

    model_config = ConfigDict(from_attributes=True)


class UserHashedPwd(User):
    hashed_password: str


class UserUpdate(BaseModel):
    name: str | None = None
    x: int | None = None
    y: int | None = None
