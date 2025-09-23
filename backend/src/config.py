from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def db_url(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def redis_url(self):
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}'

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
