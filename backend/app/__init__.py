import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from celery import Celery
from prometheus_flask_exporter import PrometheusMetrics
import structlog
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from app.api import api_bp
from app.models import db, migrate
from app.utils.config import Config
from app.utils.loggers import configure_logging


# Create Celery instance
celery = Celery(__name__)


def create_app(config_class=Config):
    """Application factory pattern"""
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    configure_logging(app)
    logger = structlog.get_logger(__name__)
    logger.info("Starting application", env=app.config["ENV"])
    
    # Setup extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)
    
    # Setup metrics
    metrics = PrometheusMetrics(app)
    metrics.info("app_info", "IntelliMail API Info", version="1.0.0")
    
    # Configure error monitoring
    if app.config["SENTRY_DSN"]:
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            environment=app.config["ENV"],
            traces_sample_rate=0.5,
        )
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    
    # Configure Celery
    celery.conf.update(app.config["CELERY_CONFIG"])
    
    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        return {"app": app, "db": db}
    
    return app 