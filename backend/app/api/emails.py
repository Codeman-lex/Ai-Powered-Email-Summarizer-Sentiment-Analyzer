from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import structlog
from marshmallow import ValidationError

from app.models.email import Email
from app.services.email_service import EmailService
from app.services.analytics_service import AnalyticsService
from app.services.ai_service import AiService

logger = structlog.get_logger(__name__)


class EmailListResource(Resource):
    """Resource for listing and creating emails"""
    
    @jwt_required()
    def get(self):
        """Get paginated list of emails with summaries and sentiment analysis"""
        try:
            user_id = get_jwt_identity()
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            filter_by = request.args.get("filter", "all")
            sort_by = request.args.get("sort", "date")
            sort_dir = request.args.get("sort_dir", "desc")
            
            email_service = EmailService()
            result = email_service.get_emails(
                user_id=user_id,
                page=page,
                per_page=per_page,
                filter_by=filter_by,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
            
            return {
                "status": "success",
                "data": result["emails"],
                "pagination": {
                    "total": result["total"],
                    "pages": result["pages"],
                    "page": page,
                    "per_page": per_page
                }
            }, 200
            
        except Exception as e:
            logger.error("Error retrieving emails", error=str(e), user_id=get_jwt_identity())
            return {"status": "error", "message": "Could not retrieve emails"}, 500


class EmailDetailResource(Resource):
    """Resource for individual email operations"""
    
    @jwt_required()
    def get(self, email_id):
        """Get details of a specific email with advanced analytics"""
        try:
            user_id = get_jwt_identity()
            
            email_service = EmailService()
            email = email_service.get_email_by_id(user_id, email_id)
            
            if not email:
                return {"status": "error", "message": "Email not found"}, 404
                
            # Get AI analysis for this email
            ai_service = AiService()
            analysis = ai_service.analyze_email_content(email)
            
            return {
                "status": "success",
                "data": {
                    "email": email,
                    "analysis": analysis
                }
            }, 200
            
        except Exception as e:
            logger.error("Error retrieving email", error=str(e), email_id=email_id, user_id=get_jwt_identity())
            return {"status": "error", "message": "Could not retrieve email details"}, 500


class EmailAnalyticsResource(Resource):
    """Resource for email analytics data"""
    
    @jwt_required()
    def get(self):
        """Get analytics about user's emails"""
        try:
            user_id = get_jwt_identity()
            time_period = request.args.get("period", "week")
            
            analytics_service = AnalyticsService()
            analytics = analytics_service.get_user_analytics(user_id, time_period)
            
            return {
                "status": "success",
                "data": analytics
            }, 200
            
        except Exception as e:
            logger.error("Error retrieving analytics", error=str(e), user_id=get_jwt_identity())
            return {"status": "error", "message": "Could not retrieve analytics data"}, 500


class EmailCategoriesResource(Resource):
    """Resource for email categories"""
    
    @jwt_required()
    def get(self):
        """Get email categories with counts"""
        try:
            user_id = get_jwt_identity()
            
            email_service = EmailService()
            categories = email_service.get_categories(user_id)
            
            return {
                "status": "success",
                "data": categories
            }, 200
            
        except Exception as e:
            logger.error("Error retrieving categories", error=str(e), user_id=get_jwt_identity())
            return {"status": "error", "message": "Could not retrieve email categories"}, 500


class EmailSearchResource(Resource):
    """Resource for semantic search of emails"""
    
    @jwt_required()
    def post(self):
        """Search emails with natural language query"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data or "query" not in data:
                return {"status": "error", "message": "Search query is required"}, 400
                
            query = data["query"]
            page = data.get("page", 1)
            per_page = data.get("per_page", 10)
            
            email_service = EmailService()
            ai_service = AiService()
            
            # Process search query with AI to improve results
            enhanced_query = ai_service.enhance_search_query(query)
            
            # Perform the search
            results = email_service.search_emails(
                user_id=user_id,
                query=enhanced_query,
                page=page,
                per_page=per_page
            )
            
            return {
                "status": "success",
                "data": results["emails"],
                "pagination": {
                    "total": results["total"],
                    "pages": results["pages"],
                    "page": page,
                    "per_page": per_page
                }
            }, 200
            
        except Exception as e:
            logger.error("Error searching emails", error=str(e), user_id=get_jwt_identity())
            return {"status": "error", "message": "Could not perform email search"}, 500


class EmailBulkActionResource(Resource):
    """Resource for bulk actions on emails"""
    
    @jwt_required()
    def post(self):
        """Perform bulk action on multiple emails"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data or "email_ids" not in data or "action" not in data:
                return {"status": "error", "message": "Email IDs and action are required"}, 400
                
            email_ids = data["email_ids"]
            action = data["action"]
            
            allowed_actions = ["archive", "delete", "mark_read", "mark_unread", "categorize"]
            if action not in allowed_actions:
                return {"status": "error", "message": f"Invalid action. Allowed actions: {', '.join(allowed_actions)}"}, 400
                
            email_service = EmailService()
            result = email_service.bulk_action(user_id, email_ids, action, data.get("params", {}))
            
            return {
                "status": "success",
                "data": {
                    "processed": result["processed"],
                    "failed": result["failed"]
                },
                "message": f"Bulk action '{action}' completed"
            }, 200
            
        except Exception as e:
            logger.error("Error performing bulk action", error=str(e), user_id=get_jwt_identity())
            return {"status": "error", "message": "Could not perform bulk action on emails"}, 500 