from datetime import date
from database.db import db
from models.employee import Employee
from services.activity_service import ActivityService
from utils.logger import get_logger

logger = get_logger()

class EmployeeService:
    @staticmethod
    def get_all_employees():
        """
        Retrieves all employees.
        """
        employees = Employee.query.all()
        return [emp.to_dict() for emp in employees]

    @staticmethod
    def get_employee_by_id(employee_id):
        """
        Retrieves an employee by database ID.
        """
        employee = db.session.get(Employee, employee_id)
        if not employee:
            return None
        return employee.to_dict()

    @staticmethod
    def create_employee(data):
        """
        Creates a new employee profile.
        Validates duplicate employee code and email.
        """
        employee_code = data.get('employee_code')
        email = data.get('email')

        # Check duplicates
        if Employee.query.filter_by(employee_code=employee_code).first():
            return {"success": False, "message": f"Employee code '{employee_code}' already exists.", "status_code": 400}
        
        if Employee.query.filter_by(email=email).first():
            return {"success": False, "message": f"Email '{email}' already registered.", "status_code": 400}

        joining_date_val = data.get('joining_date')
        if isinstance(joining_date_val, str):
            joining_date_val = date.fromisoformat(joining_date_val)

        employee = Employee(
            employee_code=employee_code,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=email,
            phone=data.get('phone'),
            department=data.get('department'),
            designation=data.get('designation'),
            joining_date=joining_date_val,
            status=data.get('status', 'ACTIVE')
        )

        db.session.add(employee)
        try:
            db.session.commit()
            
            # Log activity (since this is an employee creation, we log it with their new ID)
            ActivityService.log_activity(
                employee_id=employee.id,
                activity_type="EMPLOYEE_CREATE",
                description=f"Onboarded employee: {employee.first_name} {employee.last_name} ({employee_code})."
            )
            
            return {"success": True, "data": employee.to_dict(), "status_code": 201}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating employee: {str(e)}")
            return {"success": False, "message": "Failed to create employee.", "status_code": 500}

    @staticmethod
    def update_employee(employee_id, data):
        """
        Updates an existing employee profile.
        Validates email and employee code conflicts.
        """
        employee = db.session.get(Employee, employee_id)
        if not employee:
            return {"success": False, "message": "Employee not found.", "status_code": 404}

        employee_code = data.get('employee_code')
        email = data.get('email')

        # Check conflict for employee_code
        if employee_code and employee_code != employee.employee_code:
            conflict = Employee.query.filter_by(employee_code=employee_code).first()
            if conflict:
                return {"success": False, "message": f"Employee code '{employee_code}' is already assigned to another employee.", "status_code": 400}
            employee.employee_code = employee_code

        # Check conflict for email
        if email and email != employee.email:
            conflict = Employee.query.filter_by(email=email).first()
            if conflict:
                return {"success": False, "message": f"Email '{email}' is already registered to another employee.", "status_code": 400}
            employee.email = email

        # Update other fields if supplied
        if 'first_name' in data: employee.first_name = data['first_name']
        if 'last_name' in data: employee.last_name = data['last_name']
        if 'phone' in data: employee.phone = data['phone']
        if 'department' in data: employee.department = data['department']
        if 'designation' in data: employee.designation = data['designation']
        
        if 'joining_date' in data:
            joining_date_val = data['joining_date']
            if isinstance(joining_date_val, str):
                joining_date_val = date.fromisoformat(joining_date_val)
            employee.joining_date = joining_date_val
            
        if 'status' in data: employee.status = data['status']

        try:
            db.session.commit()
            
            # Log activity
            ActivityService.log_activity(
                employee_id=employee.id,
                activity_type="EMPLOYEE_UPDATE",
                description=f"Updated employee profile: {employee.first_name} {employee.last_name}."
            )
            
            return {"success": True, "data": employee.to_dict(), "status_code": 200}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating employee {employee_id}: {str(e)}")
            return {"success": False, "message": "Failed to update employee.", "status_code": 500}

    @staticmethod
    def delete_employee(employee_id):
        """
        Deletes an employee profile and logs the action.
        """
        employee = db.session.get(Employee, employee_id)
        if not employee:
            return {"success": False, "message": "Employee not found.", "status_code": 404}

        # Keep values for logging before deletion
        emp_id = employee.id
        emp_code = employee.employee_code
        emp_name = f"{employee.first_name} {employee.last_name}"

        db.session.delete(employee)
        try:
            db.session.commit()
            
            # Log activity (since employee is deleted, log is recorded with null/system context, noting the deleted details)
            ActivityService.log_activity(
                employee_id=None,
                activity_type="EMPLOYEE_DELETE",
                description=f"Deleted employee: {emp_name} (Code: {emp_code}, ID: {emp_id})."
            )
            
            return {"success": True, "message": "Employee profile deleted successfully.", "status_code": 200}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting employee {employee_id}: {str(e)}")
            return {"success": False, "message": "Failed to delete employee.", "status_code": 500}
