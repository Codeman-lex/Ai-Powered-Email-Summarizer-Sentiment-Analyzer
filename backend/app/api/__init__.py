from flask import Blueprint
from flask_restful import Api

# Create blueprint
api_bp = Blueprint("api", __name__)

# Create API
api = Api(api_bp)

# Import and register resources
from app.api.auth import AuthLoginResource, AuthRefreshResource, AuthRevokeResource
from app.api.emails import (
    EmailListResource, 
    EmailDetailResource, 
    EmailAnalyticsResource,
    EmailCategoriesResource,
    EmailSearchResource,
    EmailBulkActionResource
)
from app.api.user import UserProfileResource, UserSettingsResource
from app.api.health import HealthCheckResource
from app.api.swagger import SwaggerResource

# Auth endpoints
api.add_resource(AuthLoginResource, "/auth/login")
api.add_resource(AuthRefreshResource, "/auth/refresh")
api.add_resource(AuthRevokeResource, "/auth/revoke")

# Email endpoints
api.add_resource(EmailListResource, "/emails")
api.add_resource(EmailDetailResource, "/emails/<string:email_id>")
api.add_resource(EmailAnalyticsResource, "/emails/analytics")
api.add_resource(EmailCategoriesResource, "/emails/categories")
api.add_resource(EmailSearchResource, "/emails/search")
api.add_resource(EmailBulkActionResource, "/emails/bulk-action")

# User endpoints
api.add_resource(UserProfileResource, "/user/profile")
api.add_resource(UserSettingsResource, "/user/settings")

# Utility endpoints
api.add_resource(HealthCheckResource, "/health")
api.add_resource(SwaggerResource, "/docs") 