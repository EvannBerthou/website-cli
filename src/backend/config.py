from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str = ""
    login_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
