from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BrewPilot API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./brewpilot.db"
    auto_create_tables: bool = False

    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    password_hash_iterations: int = 120000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
