from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Sports Tweet Generator"
    DEBUG: bool = True
    DATABASE_URL: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_API_KEY: str
    JWT_SECRET_KEY: str
    TAVILY_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
