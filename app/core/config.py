import os

class Settings:
    ENV: str = os.getenv("ENV", "development")

settings = Settings()
