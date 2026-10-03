from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    ordenio_api_key: str

    stars_per_1000: int = 1
    free_drink_stars: int = 50
    
    jwt_secret_key: str
    jwt_expire_minutes: int = 10080

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()