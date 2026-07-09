from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from services.activity_service import ActivityService
from middleware.auth import roles_required
from utils.response import api_response, api_error

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/api/activity', methods=['GET'])
@jwt_required()
@roles_required('ADMIN', 'SECURITY_MANAGER', 'SECURITY_ANALYST', 'SOC_ENGINEER')
def get_activities():
    """
    Retrieve all activity logs.
    Restricted to Admin and Security staff.
    """
    logs = ActivityService.get_all_logs()
    serialized = [log.to_dict() for log in logs]
    return api_response(success=True, message="Activity logs retrieved successfully.", data=serialized)

@activity_bp.route('/api/activity/employee/<int:employee_id>', methods=['GET'])
@jwt_required()
def get_employee_activities(employee_id):
    """
    Retrieve activity logs for a specific employee.
    Allowed for:
      - Admin or Security roles.
      - The employee themselves (matching their own employee_id).
    """
    claims = get_jwt()
    current_role = claims.get('role', 'EMPLOYEE').upper()
    current_employee_id = claims.get('employee_id')
    
    is_privileged = current_role in ['ADMIN', 'ADMINISTRATOR', 'SECURITY_MANAGER', 'SECURITY_ANALYST', 'SOC_ENGINEER']
    is_self = current_employee_id == employee_id
    
    if not is_privileged and not is_self:
        return api_error(message="Access denied. You can only view your own activity logs.", status_code=403)
        
    logs = ActivityService.get_logs_by_employee(employee_id)
    serialized = [log.to_dict() for log in logs]
    return api_response(success=True, message="Employee activity logs retrieved successfully.", data=serialized)
