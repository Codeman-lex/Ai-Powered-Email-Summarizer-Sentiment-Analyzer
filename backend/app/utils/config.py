import os
from typing import Dict, Any


class Config:
    """Base configuration for the application."""
    
    # Flask settings
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev_key")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ENV = os.getenv("FLASK_ENV", "production")
    TESTING = False
    SERVER_NAME = os.getenv("SERVER_NAME")
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MongoDB settings
    MONGO_URI = os.getenv("MONGO_URI")
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))  # 30 days
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Celery configuration
    CELERY_CONFIG = {
        'broker_url': os.getenv("CELERY_BROKER_URL"),
        'result_backend': os.getenv("CELERY_RESULT_BACKEND"),
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'UTC',
        'enable_utc': True,
        'worker_prefetch_multiplier': 1,
        'task_acks_late': True,
        'task_reject_on_worker_lost': True,
        'task_time_limit': 600,  # 10 minutes
        'task_soft_time_limit': 540,  # 9 minutes
    }
    
    # Monitoring and error reporting
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "False").lower() == "true"
    
    # Email client settings
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    
    # AI and ML settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    USE_GPU = os.getenv("USE_GPU", "False").lower() == "true"
    
    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "60/minute")
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL")
    RATELIMIT_HEADERS_ENABLED = True
    
    # Feature flags
    ENABLE_EMAIL_CACHE = os.getenv("ENABLE_EMAIL_CACHE", "True").lower() == "true"
    ENABLE_ATTACHMENT_ANALYSIS = os.getenv("ENABLE_ATTACHMENT_ANALYSIS", "True").lower() == "true"
    ENABLE_THREAD_ANALYTICS = os.getenv("ENABLE_THREAD_ANALYTICS", "True").lower() == "true"
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding private attributes)."""
        return {key: getattr(cls, key) for key in dir(cls) 
                if not key.startswith('_') and not callable(getattr(cls, key))}


class DevelopmentConfig(Config):
    """Development configuration."""
    ENV = "development"
    DEBUG = True
    TESTING = False
    
    # Faster JWT expiration for development
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 1 day


class TestingConfig(Config):
    """Testing configuration."""
    ENV = "testing"
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Use test MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/intellimail_test")
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    ENV = "production"
    DEBUG = False
    TESTING = False
    
    # Ensure these are set in production
    @classmethod
    def validate(cls) -> None:
        """Validate production configuration."""
        required_vars = [
            "FLASK_SECRET_KEY",
            "DATABASE_URI",
            "MONGO_URI",
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND",
            "JWT_SECRET_KEY",
            "SENTRY_DSN",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "OPENAI_API_KEY",
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


# Map environment string to config class
config_by_env = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

# Get configuration based on environment
def get_config() -> Config:
    """Get the appropriate configuration based on the environment."""
    env = os.getenv("FLASK_ENV", "production")
    config_class = config_by_env.get(env, ProductionConfig)
    
    # Validate configuration in production
    if env == "production":
        config_class.validate()
        
    return config_class 