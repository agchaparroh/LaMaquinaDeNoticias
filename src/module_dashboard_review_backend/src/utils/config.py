"""
Configuration settings for Dashboard Review Backend
Loads environment variables using Pydantic BaseSettings
"""

from typing import List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase connection (required)
    supabase_url: str
    supabase_key: str
    
    # Server configuration  
    api_host: str = "0.0.0.0"
    api_port: int = 8004
    
    # CORS configuration
    cors_origins: str = "http://localhost:3001"
    
    # Optional settings
    log_level: str = "INFO"
    environment: str = "development"
    
    # Configuration for loading from .env file
    model_config = SettingsConfigDict(env_file=".env")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def LOGGING_CONFIG(self) -> Dict[str, Any]:
        """Get logging configuration for loguru"""
        from utils.logging_config import setup_logging
        return setup_logging(self.log_level, self.environment)


# Global settings instance
settings = Settings()
