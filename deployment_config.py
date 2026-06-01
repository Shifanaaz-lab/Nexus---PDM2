"""
Deployment Configuration and Infrastructure Setup
Production-ready configuration for the predictive maintenance system
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration"""
    mongodb_uri: str = "mongodb://localhost:27017/"
    database_name: str = "predictive_maintenance"
    predictions_collection: str = "predictions"
    alerts_collection: str = "alerts"
    maintenance_log_collection: str = "maintenance_log"
    connection_timeout_ms: int = 5000
    max_pool_size: int = 100
    retry_writes: bool = True


@dataclass
class ModelConfig:
    """Model configuration"""
    model_paths: List[str] = field(default_factory=lambda: [
        "optimized_xgb_rul_model.json",
        "optimized_xgb_rul_model_ensemble_1.json",
        "optimized_xgb_rul_model_ensemble_2.json"
    ])
    feature_engineer_path: str = "optimized_xgb_rul_model_feature_engineer.pkl"
    metadata_path: str = "optimized_xgb_rul_model_metadata.json"
    model_version: str = "v1.0"
    inference_timeout_ms: int = 100
    use_ensemble: bool = True
    confidence_interval_enabled: bool = True


@dataclass
class StreamingConfig:
    """Streaming pipeline configuration"""
    batch_size: int = 100
    processing_interval_seconds: float = 1.0
    max_queue_size: int = 10000
    max_history_length: int = 100
    stale_engine_threshold_seconds: float = 3600.0
    num_worker_threads: int = 4


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_real_time_monitoring: bool = True
    monitoring_window_size: int = 1000
    drift_threshold: float = 0.1
    alert_cooldown_seconds: float = 300.0
    performance_log_interval_seconds: float = 60.0
    enable_auto_retraining: bool = False
    retraining_threshold_hours: int = 24


@dataclass
class AlertingConfig:
    """Alerting configuration"""
    critical_rul_threshold: float = 100.0
    high_risk_threshold: float = 0.8
    warning_threshold: float = 0.6
    enable_email_alerts: bool = False
    enable_slack_alerts: bool = False
    email_recipients: List[str] = field(default_factory=list)
    slack_webhook_url: Optional[str] = None


@dataclass
class SystemConfig:
    """Complete system configuration"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    
    # System-wide settings
    log_level: str = "INFO"
    debug_mode: bool = False
    environment: str = "production"
    
    # Performance settings
    max_concurrent_engines: int = 1000
    feature_computation_timeout_ms: int = 50
    
    # Security settings
    enable_authentication: bool = False
    api_key_required: bool = False
    rate_limiting_enabled: bool = True


class ConfigManager:
    """Manages system configuration with validation and environment variable support"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self.config = SystemConfig()
        
        # Load configuration if file exists
        if os.path.exists(self.config_path):
            self.load_config()
        
        # Override with environment variables
        self.load_from_env()
        
        # Validate configuration
        self.validate_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # Update config with loaded data
            self._update_config_from_dict(config_data)
            
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_path}: {e}")
            print("Using default configuration")
    
    def load_from_env(self):
        """Load configuration from environment variables"""
        # Database configuration
        if os.getenv("MONGODB_URI"):
            self.config.database.mongodb_uri = os.getenv("MONGODB_URI")
        if os.getenv("DATABASE_NAME"):
            self.config.database.database_name = os.getenv("DATABASE_NAME")
        
        # Model configuration
        if os.getenv("MODEL_PATHS"):
            paths = os.getenv("MODEL_PATHS").split(",")
            self.config.model.model_paths = [p.strip() for p in paths]
        if os.getenv("FEATURE_ENGINEER_PATH"):
            self.config.model.feature_engineer_path = os.getenv("FEATURE_ENGINEER_PATH")
        
        # Streaming configuration
        if os.getenv("BATCH_SIZE"):
            self.config.streaming.batch_size = int(os.getenv("BATCH_SIZE"))
        if os.getenv("PROCESSING_INTERVAL"):
            self.config.streaming.processing_interval_seconds = float(os.getenv("PROCESSING_INTERVAL"))
        
        # Alerting configuration
        if os.getenv("CRITICAL_RUL_THRESHOLD"):
            self.config.alerting.critical_rul_threshold = float(os.getenv("CRITICAL_RUL_THRESHOLD"))
        if os.getenv("HIGH_RISK_THRESHOLD"):
            self.config.alerting.high_risk_threshold = float(os.getenv("HIGH_RISK_THRESHOLD"))
        
        # System configuration
        if os.getenv("LOG_LEVEL"):
            self.config.log_level = os.getenv("LOG_LEVEL")
        if os.getenv("ENVIRONMENT"):
            self.config.environment = os.getenv("ENVIRONMENT")
        if os.getenv("DEBUG_MODE"):
            self.config.debug_mode = os.getenv("DEBUG_MODE").lower() == "true"
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        if 'database' in config_data:
            for key, value in config_data['database'].items():
                if hasattr(self.config.database, key):
                    setattr(self.config.database, key, value)
        
        if 'model' in config_data:
            for key, value in config_data['model'].items():
                if hasattr(self.config.model, key):
                    setattr(self.config.model, key, value)
        
        if 'streaming' in config_data:
            for key, value in config_data['streaming'].items():
                if hasattr(self.config.streaming, key):
                    setattr(self.config.streaming, key, value)
        
        if 'monitoring' in config_data:
            for key, value in config_data['monitoring'].items():
                if hasattr(self.config.monitoring, key):
                    setattr(self.config.monitoring, key, value)
        
        if 'alerting' in config_data:
            for key, value in config_data['alerting'].items():
                if hasattr(self.config.alerting, key):
                    setattr(self.config.alerting, key, value)
        
        # System-wide settings
        for key in ['log_level', 'debug_mode', 'environment', 'max_concurrent_engines']:
            if key in config_data:
                setattr(self.config, key, config_data[key])
    
    def validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate database configuration
        if not self.config.database.mongodb_uri:
            errors.append("Database MongoDB URI is required")
        
        # Validate model configuration
        if not self.config.model.model_paths:
            errors.append("At least one model path is required")
        
        for model_path in self.config.model.model_paths:
            if not os.path.exists(model_path):
                errors.append(f"Model file not found: {model_path}")
        
        if not os.path.exists(self.config.model.feature_engineer_path):
            errors.append(f"Feature engineer file not found: {self.config.model.feature_engineer_path}")
        
        # Validate streaming configuration
        if self.config.streaming.batch_size <= 0:
            errors.append("Batch size must be positive")
        
        if self.config.streaming.processing_interval_seconds <= 0:
            errors.append("Processing interval must be positive")
        
        # Validate alerting configuration
        if not (0 <= self.config.alerting.critical_rul_threshold <= 1000):
            errors.append("Critical RUL threshold must be between 0 and 1000")
        
        if not (0 <= self.config.alerting.high_risk_threshold <= 1):
            errors.append("High risk threshold must be between 0 and 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def save_config(self, output_path: Optional[str] = None):
        """Save configuration to file"""
        output_path = output_path or self.config_path
        
        config_dict = {
            'database': {
                'mongodb_uri': self.config.database.mongodb_uri,
                'database_name': self.config.database.database_name,
                'predictions_collection': self.config.database.predictions_collection,
                'alerts_collection': self.config.database.alerts_collection,
                'maintenance_log_collection': self.config.database.maintenance_log_collection,
                'connection_timeout_ms': self.config.database.connection_timeout_ms,
                'max_pool_size': self.config.database.max_pool_size,
                'retry_writes': self.config.database.retry_writes
            },
            'model': {
                'model_paths': self.config.model.model_paths,
                'feature_engineer_path': self.config.model.feature_engineer_path,
                'metadata_path': self.config.model.metadata_path,
                'model_version': self.config.model.model_version,
                'inference_timeout_ms': self.config.model.inference_timeout_ms,
                'use_ensemble': self.config.model.use_ensemble,
                'confidence_interval_enabled': self.config.model.confidence_interval_enabled
            },
            'streaming': {
                'batch_size': self.config.streaming.batch_size,
                'processing_interval_seconds': self.config.streaming.processing_interval_seconds,
                'max_queue_size': self.config.streaming.max_queue_size,
                'max_history_length': self.config.streaming.max_history_length,
                'stale_engine_threshold_seconds': self.config.streaming.stale_engine_threshold_seconds,
                'num_worker_threads': self.config.streaming.num_worker_threads
            },
            'monitoring': {
                'enable_real_time_monitoring': self.config.monitoring.enable_real_time_monitoring,
                'monitoring_window_size': self.config.monitoring.monitoring_window_size,
                'drift_threshold': self.config.monitoring.drift_threshold,
                'alert_cooldown_seconds': self.config.monitoring.alert_cooldown_seconds,
                'performance_log_interval_seconds': self.config.monitoring.performance_log_interval_seconds,
                'enable_auto_retraining': self.config.monitoring.enable_auto_retraining,
                'retraining_threshold_hours': self.config.monitoring.retraining_threshold_hours
            },
            'alerting': {
                'critical_rul_threshold': self.config.alerting.critical_rul_threshold,
                'high_risk_threshold': self.config.alerting.high_risk_threshold,
                'warning_threshold': self.config.alerting.warning_threshold,
                'enable_email_alerts': self.config.alerting.enable_email_alerts,
                'enable_slack_alerts': self.config.alerting.enable_slack_alerts,
                'email_recipients': self.config.alerting.email_recipients,
                'slack_webhook_url': self.config.alerting.slack_webhook_url
            },
            'log_level': self.config.log_level,
            'debug_mode': self.config.debug_mode,
            'environment': self.config.environment,
            'max_concurrent_engines': self.config.max_concurrent_engines,
            'feature_computation_timeout_ms': self.config.feature_computation_timeout_ms,
            'enable_authentication': self.config.enable_authentication,
            'api_key_required': self.config.api_key_required,
            'rate_limiting_enabled': self.config.rate_limiting_enabled
        }
        
        try:
            with open(output_path, 'w') as f:
                if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)
            
            print(f"Configuration saved to {output_path}")
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_docker_environment(self) -> Dict[str, str]:
        """Get environment variables for Docker deployment"""
        return {
            'MONGODB_URI': self.config.database.mongodb_uri,
            'DATABASE_NAME': self.config.database.database_name,
            'MODEL_PATHS': ','.join(self.config.model.model_paths),
            'FEATURE_ENGINEER_PATH': self.config.model.feature_engineer_path,
            'BATCH_SIZE': str(self.config.streaming.batch_size),
            'PROCESSING_INTERVAL': str(self.config.streaming.processing_interval_seconds),
            'CRITICAL_RUL_THRESHOLD': str(self.config.alerting.critical_rul_threshold),
            'HIGH_RISK_THRESHOLD': str(self.config.alerting.high_risk_threshold),
            'LOG_LEVEL': self.config.log_level,
            'ENVIRONMENT': self.config.environment,
            'DEBUG_MODE': str(self.config.debug_mode).lower()
        }


def create_default_config():
    """Create default configuration file"""
    config_manager = ConfigManager()
    config_manager.save_config("config.yaml")
    print("Default configuration created: config.yaml")


def create_docker_compose():
    """Create Docker Compose file for deployment"""
    docker_compose = {
        'version': '3.8',
        'services': {
            'mongodb': {
                'image': 'mongo:6.0',
                'container_name': 'predictive_maintenance_db',
                'restart': 'unless-stopped',
                'ports': ['27017:27017'],
                'volumes': ['mongodb_data:/data/db'],
                'environment': {
                    'MONGO_INITDB_DATABASE': 'predictive_maintenance'
                }
            },
            'predictive_maintenance': {
                'build': '.',
                'container_name': 'predictive_maintenance_app',
                'restart': 'unless-stopped',
                'ports': ['8000:8000'],
                'depends_on': ['mongodb'],
                'volumes': [
                    './models:/app/models',
                    './config.yaml:/app/config.yaml',
                    './logs:/app/logs'
                ],
                'environment': {
                    'MONGODB_URI': 'mongodb://mongodb:27017/',
                    'DATABASE_NAME': 'predictive_maintenance',
                    'LOG_LEVEL': 'INFO',
                    'ENVIRONMENT': 'production'
                }
            },
            'redis': {
                'image': 'redis:7-alpine',
                'container_name': 'predictive_maintenance_cache',
                'restart': 'unless-stopped',
                'ports': ['6379:6379'],
                'volumes': ['redis_data:/data']
            }
        },
        'volumes': {
            'mongodb_data': {},
            'redis_data': {}
        }
    }
    
    with open('docker-compose.yml', 'w') as f:
        yaml.dump(docker_compose, f, default_flow_style=False)
    
    print("Docker Compose file created: docker-compose.yml")


def create_dockerfile():
    """Create Dockerfile for the application"""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs models

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "main.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("Dockerfile created: Dockerfile")


def main():
    """Main function to setup deployment configuration"""
    print("Setting up deployment configuration...")
    
    # Create default configuration
    create_default_config()
    
    # Create Docker files
    create_docker_compose()
    create_dockerfile()
    
    # Create .env file template
    env_template = """# Database Configuration
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=predictive_maintenance

# Model Configuration
MODEL_PATHS=optimized_xgb_rul_model.json,optimized_xgb_rul_model_ensemble_1.json,optimized_xgb_rul_model_ensemble_2.json
FEATURE_ENGINEER_PATH=optimized_xgb_rul_model_feature_engineer.pkl

# Streaming Configuration
BATCH_SIZE=100
PROCESSING_INTERVAL=1.0

# Alerting Configuration
CRITICAL_RUL_THRESHOLD=100.0
HIGH_RISK_THRESHOLD=0.8
WARNING_THRESHOLD=0.6

# System Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG_MODE=false

# Security
API_KEY_REQUIRED=false
RATE_LIMITING_ENABLED=true
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("Environment template created: .env.template")
    print("\nDeployment setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and customize as needed")
    print("2. Run 'docker-compose up -d' to start the services")
    print("3. Check logs with 'docker-compose logs -f predictive_maintenance'")


if __name__ == "__main__":
    main()
