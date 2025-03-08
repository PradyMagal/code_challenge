import os
import yaml
from pathlib import Path
from typing import Annotated
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and config.yaml
    """
    # API Keys from environment variables - using direct field aliases
    OPEN_AI_KEY: str
    CAL_KEY: str
    
    # App configuration from config.yaml (with defaults)
    app_name: str = "Code Challenge"
    app_version: str = "0.1.0"
    app_author: str = "Pradyun Magal"
    
    region: str = "us-west"
    debug: bool = True
    
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # Property accessors for API keys with more intuitive names
    @property
    def openai_api_key(self) -> str:
        return self.OPEN_AI_KEY
    
    @property
    def calcom_api_key(self) -> str:
        return self.CAL_KEY
    
    # Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

def get_yaml_config():
    """
    Load configuration from config.yaml
    """
    config_path = Path(__file__).parents[2] / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def create_settings():
    """
    Create settings object with values from both .env and config.yaml
    """
    settings = Settings()
    yaml_config = get_yaml_config()
    
    # Update settings from yaml config
    settings.app_name = yaml_config["app"]["name"]
    settings.app_version = yaml_config["app"]["version"]
    settings.app_author = yaml_config["app"]["author"]
    settings.region = yaml_config["environment"]["region"]
    settings.debug = yaml_config["environment"]["debug"]
    settings.timeout_seconds = yaml_config["services"]["timeout_seconds"]
    settings.max_retries = yaml_config["services"]["max_retries"]
    
    return settings

# Create a global settings object
settings = create_settings()
