from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    app_name: str = "lame-rms-backend"
    environment: str = "development"


settings = Settings()
