from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Бд
    BD_HOST: str = Field(default="localhost")
    BD_USER: str = Field(default="postgres")
    BD_PASSWORD: str
    BD_NAME: str 
    
    # JWT 
    SECRET_KEY: str = Field(default="zlqp1937")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)
    
    model_config = SettingsConfigDict(
        env_file=".env", # ../.env # .env (для миграций для докера)
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    def get_database_url(self):
        """Собирает URL для подключения к PostgreSQL"""
        return (
            f"postgresql://{self.BD_USER}:{self.BD_PASSWORD}"
            f"@{self.BD_HOST}/{self.BD_NAME}"
        )

settings = Settings()

print(settings.get_database_url())