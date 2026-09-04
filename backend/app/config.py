from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./test.db"
    jwt_secret: str = "secret"
    jwt_expiry_minutes: int = 480
    admin_email: str = "admin@peblo.tv"
    admin_password: str = "admin"
    editor_email: str = "editor@peblo.tv"
    editor_password: str = "editor"
    storage_backend: str = "local"
    storage_path: str = "/data/storage"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    class Config:
        env_file = ".env"

settings = Settings()
