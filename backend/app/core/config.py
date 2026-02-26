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

    ai_provider: str = "rules"
    ai_llm_base_url: str | None = None
    ai_llm_api_key: str | None = None
    ai_llm_model: str | None = None
    ai_llm_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
