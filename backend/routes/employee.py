from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from services.employee_service import EmployeeService
from middleware.auth import roles_required
from utils.validators import EmployeeSchema
from utils.response import api_response, api_error
from marshmallow import ValidationError

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/api/employees', methods=['GET'])
@jwt_required()
@roles_required('ADMIN', 'SECURITY_MANAGER', 'SECURITY_ANALYST', 'SOC_ENGINEER')
def get_employees():
    """
    Get all employee profiles.
    Restricted to Admins and Security personnel.
    """
    employees = EmployeeService.get_all_employees()
    return api_response(success=True, message="Employees retrieved successfully.", data=employees)

@employee_bp.route('/api/employees/<int:employee_id>', methods=['GET'])
@jwt_required()
def get_employee(employee_id):
    """
    Get a single employee profile.
    Allowed for:
      - Admin or Security roles.
      - The employee themselves (matching their own employee_id).
    """
    claims = get_jwt()
    current_role = claims.get('role', 'EMPLOYEE').upper()
    current_employee_id = claims.get('employee_id')
    
    # Check authorization: user can view if admin/security, or if viewing their own profile
    is_privileged = current_role in ['ADMIN', 'ADMINISTRATOR', 'SECURITY_MANAGER', 'SECURITY_ANALYST', 'SOC_ENGINEER']
    is_self = current_employee_id == employee_id
    
    if not is_privileged and not is_self:
        return api_error(message="Access denied. You can only view your own profile.", status_code=403)

    employee = EmployeeService.get_employee_by_id(employee_id)
    if not employee:
        return api_error(message="Employee profile not found.", status_code=404)
        
    return api_response(success=True, message="Employee profile retrieved successfully.", data=employee)

@employee_bp.route('/api/employees', methods=['POST'])
@jwt_required()
@roles_required('ADMIN', 'SECURITY_MANAGER')
def create_employee():
    """
    Create a new employee profile.
    Restricted to Admin and Security Manager roles.
    """
    json_data = request.get_json()
    if not json_data:
        return api_error(message="No input data provided.", status_code=400)
        
    try:
        data = EmployeeSchema().load(json_data)
    except ValidationError as err:
        return api_error(message="Validation error.", errors=err.messages, status_code=400)
        
    result = EmployeeService.create_employee(data)
    if not result["success"]:
        return api_error(message=result["message"], status_code=result["status_code"])
        
    return api_response(
        success=True,
        message="Employee profile created successfully.",
        data=result.get("data"),
        status_code=result["status_code"]
    )

@employee_bp.route('/api/employees/<int:employee_id>', methods=['PUT'])
@jwt_required()
@roles_required('ADMIN', 'SECURITY_MANAGER')
def update_employee(employee_id):
    """
    Update an existing employee profile.
    Restricted to Admin and Security Manager roles.
    """
    json_data = request.get_json()
    if not json_data:
        return api_error(message="No input data provided.", status_code=400)
        
    try:
        # Partial validation: permit partial updates
        data = EmployeeSchema().load(json_data, partial=True)
    except ValidationError as err:
        return api_error(message="Validation error.", errors=err.messages, status_code=400)
        
    result = EmployeeService.update_employee(employee_id, data)
    if not result["success"]:
        return api_error(message=result["message"], status_code=result["status_code"])
        
    return api_response(
        success=True,
        message="Employee profile updated successfully.",
        data=result.get("data"),
        status_code=result["status_code"]
    )

@employee_bp.route('/api/employees/<int:employee_id>', methods=['DELETE'])
@jwt_required()
@roles_required('ADMIN')
def delete_employee(employee_id):
    """
    Delete an employee profile.
    Restricted to Admin role only.
    """
    result = EmployeeService.delete_employee(employee_id)
    if not result["success"]:
        return api_error(message=result["message"], status_code=result["status_code"])
        
    return api_response(
        success=True,
        message=result["message"],
        status_code=result["status_code"]
    )
