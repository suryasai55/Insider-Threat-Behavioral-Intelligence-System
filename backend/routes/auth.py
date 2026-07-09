from flask import Blueprint, request, render_template, redirect, url_for
from flask_jwt_extended import (
    jwt_required, 
    get_jwt_identity, 
    get_jwt, 
    verify_jwt_in_request
)
from services.auth_service import AuthService
from utils.validators import LoginSchema, RegisterSchema
from utils.response import api_response, api_error
from utils.logger import get_logger
from marshmallow import ValidationError

logger = get_logger()
auth_bp = Blueprint('auth', __name__)

# ==========================================
# REST API ENDPOINTS
# ==========================================

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """
    API endpoint to register a new user and link employee details.
    """
    json_data = request.get_json()
    if not json_data:
        return api_error(message="No input data provided.", status_code=400)
        
    try:
        data = RegisterSchema().load(json_data)
    except ValidationError as err:
        return api_error(message="Validation error.", errors=err.messages, status_code=400)
        
    result = AuthService.register_user(data)
    if not result["success"]:
        return api_error(message=result["message"], status_code=result["status_code"])
        
    return api_response(
        success=True,
        message=result["message"],
        data=result.get("data"),
        status_code=result["status_code"]
    )

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """
    API endpoint to authenticate user credentials.
    """
    json_data = request.get_json()
    if not json_data:
        return api_error(message="No input data provided.", status_code=400)
        
    try:
        data = LoginSchema().load(json_data)
    except ValidationError as err:
        return api_error(message="Validation error.", errors=err.messages, status_code=400)
        
    result = AuthService.login_user(data["username"], data["password"])
    if not result["success"]:
        return api_error(message=result["message"], status_code=result["status_code"])
        
    return api_response(
        success=True,
        message=result["message"],
        data=result.get("data"),
        status_code=result["status_code"]
    )

@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def api_logout():
    """
    API endpoint to log out user.
    """
    user_id = get_jwt_identity()
    result = AuthService.logout_user(user_id)
    if not result["success"]:
        return api_error(message=result["message"], status_code=result["status_code"])
    return api_response(success=True, message=result["message"], status_code=result["status_code"])

@auth_bp.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def api_refresh():
    """
    API endpoint to generate a new access token using a refresh token.
    """
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Rebuild user claims
    from models.user import User
    from database.db import db
    user = db.session.get(User, user_id)
    if not user:
        return api_error(message="User not found.", status_code=404)
        
    new_claims = {
        "role": user.role.role_name if user.role else "EMPLOYEE",
        "username": user.username,
        "employee_id": user.employee_id
    }
    
    from flask_jwt_extended import create_access_token
    new_access_token = create_access_token(identity=str(user.id), additional_claims=new_claims)
    
    return api_response(
        success=True,
        message="Token refreshed successfully.",
        data={"access_token": new_access_token}
    )

@auth_bp.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def api_profile():
    """
    API endpoint to fetch current user's profile.
    """
    user_id = get_jwt_identity()
    result = AuthService.get_profile(user_id)
    if not result["success"]:
        return api_error(message=result["message"], status_code=result["status_code"])
    return api_response(success=True, message="Profile retrieved successfully.", data=result["data"], status_code=result["status_code"])


# ==========================================
# WEB TEMPLATE ROUTING (HTML Views)
# ==========================================

@auth_bp.route('/', methods=['GET'])
def index():
    return redirect(url_for('auth.web_login'))

@auth_bp.route('/login', methods=['GET'])
def web_login():
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET'])
def web_register():
    return render_template('register.html')

@auth_bp.route('/profile', methods=['GET'])
def web_profile():
    return render_template('profile.html')
