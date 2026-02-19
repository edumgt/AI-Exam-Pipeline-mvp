from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    PUBLIC_BASE_URL: str = "http://localhost:8080"

    POSTGRES_DB: str = "exam_ai"
    POSTGRES_USER: str = "exam_ai"
    POSTGRES_PASSWORD: str = "exam_ai_pw"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    DATA_ROOT: str = "/data"
    CORS_ORIGINS: str = "http://localhost:8080"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

settings = Settings()
