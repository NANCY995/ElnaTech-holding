"""Configuration centralisée de l'application Elna Pay"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Paramètres de configuration"""
    APP_NAME: str = "Elna Pay"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Base de données
    DATABASE_URL: str = "sqlite:///./elna_pay.db"
    
    # Sécurité
    SECRET_KEY: str = "elna-pay-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # IA - Détection de fraude
    FRAUD_DETECTION_ENABLED: bool = True
    ANOMALY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
