import os
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from config import config_instance
from database.db import db, migrate, bcrypt
from routes.auth import auth_bp
from routes.employee import employee_bp
from routes.activity import activity_bp
from routes.admin import admin_bp
from utils.logger import get_logger
from utils.response import api_error

# Initialize logger
logger = get_logger()

def create_app(config_class=config_instance):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    
    # Configure JWT
    jwt = JWTManager(app)
    
    # Configure CORS
    CORS(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(admin_bp)

    # ==========================================
    # CENTRALIZED ERROR HANDLING
    # ==========================================

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        logger.warning(f"Validation Failure: {e.messages}")
        return api_error(message="Input validation failed.", errors=e.messages, status_code=400)

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        logger.warning(f"HTTP Exception: {e.description} (Code: {e.code})")
        return api_error(message=e.description, status_code=e.code)

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(e):
        logger.error(f"Database Failure: {str(e)}", exc_info=True)
        return api_error(message="A database system error occurred. Action rolled back.", status_code=500)

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger.error(f"Unhandled Application Exception: {str(e)}", exc_info=True)
        return api_error(message="An unexpected system error occurred. Please contact security team.", status_code=500)

    # ==========================================
    # REQUEST LOGGING MIDDLEWARE
    # ==========================================

    @app.before_request
    def log_incoming_request():
        # Exclude static/assets logging if any to save log size
        if not request.path.startswith('/static'):
            logger.info(f"API Request: {request.method} {request.path} from IP: {request.remote_addr} - Agent: {request.user_agent.string[:100]}")

    # ==========================================
    # DATABASE SEEDING
    # ==========================================
    with app.app_context():
        try:
            # Create tables if they do not exist (useful for SQLite out-of-the-box run)
            db.create_all()
            
            # Seed Roles
            from models.role import Role
            roles_to_seed = ['ADMINISTRATOR', 'ADMIN', 'SECURITY_ANALYST', 'SOC_ENGINEER', 'SECURITY_MANAGER', 'EMPLOYEE']
            for role_name in roles_to_seed:
                if not Role.query.filter_by(role_name=role_name).first():
                    r = Role(role_name=role_name)
                    db.session.add(r)
            db.session.commit()
            
            # Seed Default Administrator account if none exists
            from models.user import User
            admin_role = Role.query.filter_by(role_name='ADMINISTRATOR').first()
            if admin_role and not User.query.filter_by(username='admin').first():
                admin_pass_hash = bcrypt.generate_password_hash('password123').decode('utf-8')
                
                # Optionally seed linked employee profile for admin
                from models.employee import Employee
                from datetime import date
                
                admin_employee = Employee.query.filter_by(employee_code='EMP0001').first()
                if not admin_employee:
                    admin_employee = Employee(
                        employee_code='EMP0001',
                        first_name='Admin',
                        last_name='User',
                        email='admin@enterprise-security.com',
                        phone='+1234567890',
                        department='CyberSecurity Operations',
                        designation='Chief Security Architect',
                        joining_date=date.today(),
                        status='ACTIVE'
                    )
                    db.session.add(admin_employee)
                    db.session.flush() # get id
                
                admin_user = User(
                    username='admin',
                    password_hash=admin_pass_hash,
                    role_id=admin_role.id,
                    employee_id=admin_employee.id
                )
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Default administrator account successfully seeded. Username: 'admin', Password: 'password123'")
        except Exception as e:
            logger.error(f"Error seeding database: {str(e)}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
