"""
Configuration settings for Finance Portfolio Copilot
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    gemini_api_key: str = "AIzaSyDMgAhfKIwe_xEarHd-BnDE13UjF2z0gKI"
    alpha_vantage_api_key: str = "UL594TPTS0ZDG3RT"
    openai_api_key: str = ""
    
    # Database
    database_url: str = "sqlite:///./data/finance_copilot.db"
    
    # JWT Authentication
    secret_key: str = "your_super_secret_key_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Pathway Settings
    pathway_host: str = "localhost"
    pathway_port: int = 8001
    
    # Data Paths
    docs_path: str = "./data/docs"
    prices_path: str = "./data/prices"
    portfolios_path: str = "./data/portfolios"
    
    # Market Data Settings
    price_update_interval: int = 60  # seconds
    news_update_interval: int = 300  # seconds
    
    # Frontend URL
    frontend_url: str = "http://localhost:3000"
    
    # Gemini Model Settings
    gemini_model: str = "gemini-pro"
    gemini_temperature: float = 0.3
    
    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
