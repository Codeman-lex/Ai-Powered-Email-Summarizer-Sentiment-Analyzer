import os
import logging
import logging.config
import sys
import time
from typing import Any, Dict, Optional
import structlog
from pythonjsonlogger import jsonlogger
from flask import Flask, request, g


def configure_logging(app: Flask) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        app: Flask application instance
    """
    # Set log level based on environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Configure standard logging
    processors = [
        # Add timestamps and log level names
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        
        # Add request context information
        add_request_context,
        
        # Add app context
        structlog.processors.ContextRenderer(
            processors=[structlog.processors.KeyValueRenderer()]
        ),
        
        # Format for production or development
        structlog.processors.JSONRenderer() if app.config["ENV"] == "production" 
        else structlog.dev.ConsoleRenderer(colors=True)
    ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure Python's standard logging
    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter for production
    if app.config["ENV"] == "production":
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(levelname)s %(name)s %(message)s"
        )
        handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(numeric_level)
    
    # Set level for external libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("gunicorn").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Register request handlers
    app.before_request(log_request_start)
    app.after_request(log_request_end)


def add_request_context(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request context to the log entry if available."""
    if request:
        event_dict["http_method"] = request.method
        event_dict["path"] = request.path
        
        # Add request ID if available
        if hasattr(g, "request_id"):
            event_dict["request_id"] = g.request_id
            
        # Add user ID if available
        if hasattr(g, "user_id"):
            event_dict["user_id"] = g.user_id
    
    return event_dict


def log_request_start() -> None:
    """Log the start of a request."""
    g.request_start_time = time.time()
    g.request_id = request.headers.get("X-Request-ID", "")
    
    # Extract user ID from token if available (usually set by auth middleware)
    user_id = getattr(g, "user_id", None)
    
    logger = structlog.get_logger(__name__)
    logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        user_agent=request.user_agent.string,
        user_id=user_id,
    )


def log_request_end(response: Any) -> Any:
    """
    Log the end of a request including response status and timing.
    
    Args:
        response: Flask response object
        
    Returns:
        Flask response object
    """
    if hasattr(g, "request_start_time"):
        duration_ms = int((time.time() - g.request_start_time) * 1000)
        
        logger = structlog.get_logger(__name__)
        logger.info(
            "Request finished",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=duration_ms,
            content_length=response.content_length,
        )
    
    return response


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name) 