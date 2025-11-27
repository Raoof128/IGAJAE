from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "IGA Platform"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Simulated Connector Settings
    AZURE_AD_ENABLED: bool = True
    GITHUB_ENABLED: bool = True
    SLACK_ENABLED: bool = True
    JIRA_ENABLED: bool = True

    # Policy Settings
    BIRTHRIGHT_DEPARTMENTS: List[str] = ["Engineering", "Sales", "Marketing", "HR"]

    class Config:
        env_file = ".env"


settings = Settings()
