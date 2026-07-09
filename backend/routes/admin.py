from flask import Blueprint
from flask_jwt_extended import jwt_required
from middleware.auth import roles_required
from models.user import User
from models.employee import Employee
from models.activity_log import ActivityLog
from utils.response import api_response

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/system-summary', methods=['GET'])
@jwt_required()
@roles_required('ADMIN')
def get_system_summary():
    """
    Get a high-level metadata summary of the system.
    Restricted to Admin only.
    """
    total_users = User.query.count()
    total_employees = Employee.query.count()
    total_logs = ActivityLog.query.count()
    
    # Active vs Inactive count
    active_employees = Employee.query.filter_by(status='ACTIVE').count()
    inactive_employees = total_employees - active_employees
    
    data = {
        "system_status": "ONLINE",
        "metrics": {
            "total_users": total_users,
            "total_employees": total_employees,
            "active_employees": active_employees,
            "inactive_employees": inactive_employees,
            "total_activity_logs": total_logs
        }
    }
    
    return api_response(success=True, message="System summary retrieved successfully.", data=data)
