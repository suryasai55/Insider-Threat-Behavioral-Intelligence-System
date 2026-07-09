from datetime import date
from flask_jwt_extended import create_access_token, create_refresh_token
from database.db import db, bcrypt
from models.user import User
from models.employee import Employee
from models.role import Role
from services.activity_service import ActivityService
from utils.logger import get_logger

logger = get_logger()

class AuthService:
    @staticmethod
    def register_user(data):
        """
        Registers a new User and creates/links an Employee profile if provided.
        """
        username = data.get('username')
        password = data.get('password')
        role_name = data.get('role_name', 'EMPLOYEE').upper()
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            return {"success": False, "message": "Username already exists.", "status_code": 400}
            
        # Get or create Role
        role = Role.query.filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name)
            db.session.add(role)
            db.session.flush()

        employee = None
        # Check if employee details are provided
        employee_code = data.get('employee_code')
        email = data.get('email')
        
        if employee_code or email:
            if not employee_code or not email:
                return {"success": False, "message": "Both employee_code and email are required to link an employee profile.", "status_code": 400}
                
            # Check duplicates
            if Employee.query.filter_by(employee_code=employee_code).first():
                return {"success": False, "message": f"Employee code '{employee_code}' already exists.", "status_code": 400}
            if Employee.query.filter_by(email=email).first():
                return {"success": False, "message": f"Email '{email}' already registered.", "status_code": 400}
                
            # Create Employee
            joining_date_val = data.get('joining_date')
            if isinstance(joining_date_val, str):
                joining_date_val = date.fromisoformat(joining_date_val)
            elif not joining_date_val:
                joining_date_val = date.today()

            employee = Employee(
                employee_code=employee_code,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                email=email,
                phone=data.get('phone'),
                department=data.get('department', 'Unassigned'),
                designation=data.get('designation', 'Staff'),
                joining_date=joining_date_val,
                status='ACTIVE'
            )
            db.session.add(employee)
            db.session.flush()  # get employee.id

        # Hash password and create User
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            password_hash=password_hash,
            role_id=role.id,
            employee_id=employee.id if employee else None
        )
        db.session.add(user)
        
        try:
            db.session.commit()
            
            # Log activity
            emp_id = employee.id if employee else None
            ActivityService.log_activity(
                employee_id=emp_id,
                activity_type="EMPLOYEE_CREATE" if employee else "USER_REGISTER",
                description=f"User '{username}' registered successfully as role {role_name}."
            )
            
            return {
                "success": True,
                "message": "User registered successfully.",
                "data": user.to_dict(),
                "status_code": 201
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {str(e)}")
            return {"success": False, "message": "Database transaction failed.", "status_code": 500}

    @staticmethod
    def login_user(username, password):
        """
        Authenticates a user, logs the success/failure, and returns access/refresh JWT tokens.
        """
        user = User.query.filter_by(username=username).first()
        
        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            # Log failure
            # If the user exists, log with their employee ID
            emp_id = user.employee_id if user else None
            ActivityService.log_activity(
                employee_id=emp_id,
                activity_type="LOGIN_FAILURE",
                description=f"Failed login attempt for username '{username}'."
            )
            return {"success": False, "message": "Invalid username or password.", "status_code": 401}
            
        # Success - Generate Tokens
        # Additional claims for JWT
        claims = {
            "role": user.role.role_name if user.role else "EMPLOYEE",
            "username": user.username,
            "employee_id": user.employee_id
        }
        
        # Create access and refresh tokens
        access_token = create_access_token(identity=str(user.id), additional_claims=claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=claims)
        
        # Log activity
        ActivityService.log_activity(
            employee_id=user.employee_id,
            activity_type="LOGIN_SUCCESS",
            description=f"User '{username}' successfully logged in."
        )
        
        return {
            "success": True,
            "message": "Login successful.",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_dict()
            },
            "status_code": 200
        }

    @staticmethod
    def logout_user(user_id):
        """
        Logs a user logout event.
        """
        user = db.session.get(User, user_id)
        if user:
            ActivityService.log_activity(
                employee_id=user.employee_id,
                activity_type="LOGOUT",
                description=f"User '{user.username}' logged out."
            )
            return {"success": True, "message": "Logout successful.", "status_code": 200}
        return {"success": False, "message": "User not found.", "status_code": 404}

    @staticmethod
    def get_profile(user_id):
        """
        Retrieves user profile data and linked employee details.
        """
        user = db.session.get(User, user_id)
        if not user:
            return {"success": False, "message": "User not found.", "status_code": 404}
            
        user_data = user.to_dict()
        if user.employee:
            user_data["employee_details"] = user.employee.to_dict()
            
        return {"success": True, "data": user_data, "status_code": 200}
