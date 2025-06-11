"""
Configuration management for Experiment Tracking service
"""

import os
from typing import Optional
from pydantic import Field, BaseModel

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback implementation for CI/environments without pydantic-settings
    class BaseSettings(BaseModel):
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "experiment-tracking"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8003, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database settings
    database_url: str = Field(
        default="postgresql://mlops:mlops123@localhost:5432/experiment_tracking",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=0, env="DATABASE_MAX_OVERFLOW")
    
    # Redis settings (optional for caching)
    redis_url: Optional[str] = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")  # 1 hour default
    redis_enabled: bool = Field(default=True, env="REDIS_ENABLED")
    
    # Storage settings (MinIO/S3)
    storage_backend: str = Field(default="minio", env="STORAGE_BACKEND")
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    
    # Storage buckets
    storage_bucket_experiments: str = Field(default="experiments", env="STORAGE_BUCKET_EXPERIMENTS")
    storage_bucket_artifacts: str = Field(default="artifacts", env="STORAGE_BUCKET_ARTIFACTS")
    storage_bucket_visualizations: str = Field(default="visualizations", env="STORAGE_BUCKET_VISUALIZATIONS")
    
    # MLOps service integration
    registry_service_url: str = Field(default="http://localhost:8000", env="MODEL_REGISTRY_URL")
    pipeline_orchestrator_url: str = Field(default="http://localhost:8001", env="PIPELINE_ORCHESTRATOR_URL")
    feature_store_url: str = Field(default="http://localhost:8002", env="FEATURE_STORE_URL")
    
    # Experiment settings
    max_concurrent_experiments: int = Field(default=50, env="MAX_CONCURRENT_EXPERIMENTS")
    max_runs_per_experiment: int = Field(default=1000, env="MAX_RUNS_PER_EXPERIMENT")
    default_experiment_ttl_days: int = Field(default=365, env="DEFAULT_EXPERIMENT_TTL_DAYS")
    
    # Metrics and logging
    max_metrics_per_run: int = Field(default=10000, env="MAX_METRICS_PER_RUN")
    metric_batch_size: int = Field(default=100, env="METRIC_BATCH_SIZE")
    enable_real_time_metrics: bool = Field(default=True, env="ENABLE_REAL_TIME_METRICS")
    
    # Visualization settings
    enable_real_time_plots: bool = Field(default=True, env="ENABLE_REAL_TIME_PLOTS")
    plot_backend: str = Field(default="plotly", env="PLOT_BACKEND")  # plotly, matplotlib
    max_concurrent_visualizations: int = Field(default=50, env="MAX_CONCURRENT_VISUALIZATIONS")
    
    # Security settings
    secret_key: str = Field(
        default="experiment-tracking-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    
    # Hyperparameter optimization
    enable_hpo: bool = Field(default=True, env="ENABLE_HPO")
    max_hpo_trials: int = Field(default=1000, env="MAX_HPO_TRIALS")
    hpo_backend: str = Field(default="optuna", env="HPO_BACKEND")  # optuna, hyperopt
    
    # Resource limits
    max_artifact_size_mb: int = Field(default=1000, env="MAX_ARTIFACT_SIZE_MB")  # 1GB
    max_log_size_mb: int = Field(default=100, env="MAX_LOG_SIZE_MB")  # 100MB
    
    # Integration timeouts
    service_timeout_seconds: int = Field(default=30, env="SERVICE_TIMEOUT_SECONDS")
    registry_service_timeout: int = Field(default=10, env="MODEL_REGISTRY_TIMEOUT")
    pipeline_orchestrator_timeout: int = Field(default=30, env="PIPELINE_ORCHESTRATOR_TIMEOUT")
    feature_store_timeout: int = Field(default=5, env="FEATURE_STORE_TIMEOUT")
    
    # Monitoring and observability
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    metrics_port: int = Field(default=9003, env="METRICS_PORT")
    
    # Healthcare-specific settings
    enable_healthcare_validation: bool = Field(default=True, env="ENABLE_HEALTHCARE_VALIDATION")
    required_healthcare_metrics: list = Field(
        default=["accuracy", "crisis_detection_rate", "response_quality"],
        env="REQUIRED_HEALTHCARE_METRICS"
    )
    min_crisis_detection_rate: float = Field(default=0.99, env="MIN_CRISIS_DETECTION_RATE")
    min_response_quality_score: float = Field(default=0.8, env="MIN_RESPONSE_QUALITY_SCORE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings (useful for testing)"""
    global _settings
    _settings = Settings()
    return _settings


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings"""
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    
    # Production security
    minio_secure: bool = True
    redis_enabled: bool = True
    
    # Production performance
    database_pool_size: int = 50
    max_concurrent_experiments: int = 200
    max_concurrent_visualizations: int = 100


class TestingSettings(Settings):
    """Testing environment settings"""
    environment: str = "testing"
    debug: bool = True
    log_level: str = "DEBUG"
    
    # Use in-memory databases for testing
    database_url: str = "sqlite:///:memory:"
    redis_enabled: bool = False


def get_environment_settings() -> Settings:
    """Get environment-specific settings"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()