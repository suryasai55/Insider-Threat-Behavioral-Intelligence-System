from flask import request
from database.db import db
from models.activity_log import ActivityLog
from utils.logger import get_logger

logger = get_logger()

class ActivityService:
    @staticmethod
    def log_activity(employee_id, activity_type, description):
        """
        Record a security/activity log in the database.
        Automatically resolves ip_address and device_name if inside a Flask request context.
        """
        ip_address = None
        device_name = None
        
        try:
            # Check if running within a Flask request context
            if request:
                # Capture client IP (taking headers like X-Forwarded-For into account)
                if request.headers.getlist("X-Forwarded-For"):
                    ip_address = request.headers.getlist("X-Forwarded-For")[0]
                else:
                    ip_address = request.remote_addr
                
                # Capture User-Agent for device info
                device_name = request.user_agent.string if request.user_agent else "Unknown"
        except RuntimeError:
            # Occurs when called outside of request context (e.g. testing or CLI)
            pass

        try:
            activity = ActivityLog(
                employee_id=employee_id,
                activity_type=activity_type,
                description=description,
                ip_address=ip_address,
                device_name=device_name
            )
            db.session.add(activity)
            db.session.commit()
            
            logger.info(f"Activity Logged: {activity_type} - {description} (Employee ID: {employee_id})")
            return activity
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record activity log: {str(e)}")
            return None
            
    @staticmethod
    def get_all_logs(limit=100, offset=0):
        return ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).offset(offset).all()
        
    @staticmethod
    def get_logs_by_employee(employee_id, limit=100, offset=0):
        return ActivityLog.query.filter_by(employee_id=employee_id).order_by(ActivityLog.timestamp.desc()).limit(limit).offset(offset).all()
