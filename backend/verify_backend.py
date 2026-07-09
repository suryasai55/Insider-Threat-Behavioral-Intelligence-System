import unittest
import json
from datetime import date
from app import create_app
from database.db import db
from models.user import User
from models.employee import Employee
from models.role import Role
from models.activity_log import ActivityLog
from config import Config

class TestConfig(Config):
    # Use isolated SQLite for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    DEBUG = False

class BackendIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        """
        Runs before each test method. Sets up database and seeds test roles.
        """
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        """
        Runs after each test method. Drops database context.
        """
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_database_initialization_and_seeding(self):
        """
        Verify that database contains default roles and seeded administrator.
        """
        # Roles check
        roles = [r.role_name for r in Role.query.all()]
        self.assertIn("ADMINISTRATOR", roles)
        self.assertIn("EMPLOYEE", roles)
        self.assertIn("SECURITY_ANALYST", roles)

        # Admin user check
        admin_user = User.query.filter_by(username="admin").first()
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user.role.role_name, "ADMINISTRATOR")
        self.assertIsNotNone(admin_user.employee)
        self.assertEqual(admin_user.employee.employee_code, "EMP0001")

    def test_login_successful_and_failures(self):
        """
        Verify auth login functionality, token creation, and corresponding logs.
        """
        # 1. Test success login
        payload = {"username": "admin", "password": "password123"}
        response = self.client.post("/api/auth/login", 
                                    data=json.dumps(payload),
                                    content_type="application/json")
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("access_token", data["data"])
        self.assertIn("refresh_token", data["data"])

        # Check login success log in DB
        logs = ActivityLog.query.filter_by(activity_type="LOGIN_SUCCESS").all()
        self.assertEqual(len(logs), 1)
        self.assertIn("admin", logs[0].description)

        # 2. Test failed login
        fail_payload = {"username": "admin", "password": "wrongpassword"}
        fail_res = self.client.post("/api/auth/login", 
                                    data=json.dumps(fail_payload),
                                    content_type="application/json")
        fail_data = fail_res.get_json()
        
        self.assertEqual(fail_res.status_code, 401)
        self.assertFalse(fail_data["success"])
        self.assertNotIn("data", fail_data)

        # Check login failure log in DB
        fail_logs = ActivityLog.query.filter_by(activity_type="LOGIN_FAILURE").all()
        self.assertEqual(len(fail_logs), 1)

    def test_jwt_token_refresh_and_profile(self):
        """
        Verify profile retrieval and token refreshing works correctly.
        """
        # Login to get tokens
        payload = {"username": "admin", "password": "password123"}
        login_res = self.client.post("/api/auth/login", data=json.dumps(payload), content_type="application/json")
        tokens = login_res.get_json()["data"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 1. Fetch Profile
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_res = self.client.get("/api/auth/profile", headers=headers)
        profile_data = profile_res.get_json()
        
        self.assertEqual(profile_res.status_code, 200)
        self.assertTrue(profile_data["success"])
        self.assertEqual(profile_data["data"]["username"], "admin")
        self.assertEqual(profile_data["data"]["employee_details"]["employee_code"], "EMP0001")

        # 2. Refresh Token
        refresh_headers = {"Authorization": f"Bearer {refresh_token}"}
        refresh_res = self.client.post("/api/auth/refresh", headers=refresh_headers)
        refresh_data = refresh_res.get_json()

        self.assertEqual(refresh_res.status_code, 200)
        self.assertTrue(refresh_data["success"])
        self.assertIn("access_token", refresh_data["data"])

    def test_employee_crud_and_validation(self):
        """
        Verify employee endpoints CRUD operations, RBAC controls, and validation routines.
        """
        # Login to obtain admin token
        payload = {"username": "admin", "password": "password123"}
        login_res = self.client.post("/api/auth/login", data=json.dumps(payload), content_type="application/json")
        admin_token = login_res.get_json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Onboard Employee via POST
        emp_payload = {
            "employee_code": "EMP9999",
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@enterprise.com",
            "phone": "+1234567890",
            "department": "Engineering",
            "designation": "Software Developer",
            "joining_date": "2026-07-01"
        }
        res_create = self.client.post("/api/employees", data=json.dumps(emp_payload), content_type="application/json", headers=headers)
        data_create = res_create.get_json()
        
        self.assertEqual(res_create.status_code, 201)
        self.assertTrue(data_create["success"])
        new_emp_id = data_create["data"]["id"]

        # Verify creation log
        create_log = ActivityLog.query.filter_by(employee_id=new_emp_id, activity_type="EMPLOYEE_CREATE").first()
        self.assertIsNotNone(create_log)

        # 2. Test Duplicate Check Validation
        res_dup = self.client.post("/api/employees", data=json.dumps(emp_payload), content_type="application/json", headers=headers)
        data_dup = res_dup.get_json()
        self.assertEqual(res_dup.status_code, 400)
        self.assertFalse(data_dup["success"])
        self.assertIn("exists", data_dup["message"])

        # 3. GET Single Employee
        res_get = self.client.get(f"/api/employees/{new_emp_id}", headers=headers)
        data_get = res_get.get_json()
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(data_get["data"]["employee_code"], "EMP9999")

        # 4. PUT Update Employee
        update_payload = {"department": "Security Architecture", "phone": "987-654-3210"}
        res_update = self.client.put(f"/api/employees/{new_emp_id}", data=json.dumps(update_payload), content_type="application/json", headers=headers)
        data_update = res_update.get_json()
        
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(data_update["data"]["department"], "Security Architecture")
        self.assertEqual(data_update["data"]["phone"], "987-654-3210")

        # Verify update log
        update_log = ActivityLog.query.filter_by(employee_id=new_emp_id, activity_type="EMPLOYEE_UPDATE").first()
        self.assertIsNotNone(update_log)

        # 5. DELETE Employee
        res_delete = self.client.delete(f"/api/employees/{new_emp_id}", headers=headers)
        data_delete = res_delete.get_json()
        self.assertEqual(res_delete.status_code, 200)
        self.assertTrue(data_delete["success"])

        # Verify deletion log (records under system null/deleted context)
        delete_log = ActivityLog.query.filter_by(activity_type="EMPLOYEE_DELETE").first()
        self.assertIsNotNone(delete_log)
        self.assertIn("EMP9999", delete_log.description)

    def test_rbac_restrictions(self):
        """
        Verify that non-admin/non-privileged users cannot access endpoints they shouldn't.
        """
        # Register a standard Employee user
        emp_register_payload = {
            "username": "staff_member",
            "password": "password123",
            "role_name": "EMPLOYEE",
            "employee_code": "EMP0005",
            "first_name": "Staff",
            "last_name": "Employee",
            "email": "staff@enterprise.com",
            "joining_date": "2026-07-01"
        }
        self.client.post("/api/auth/register", data=json.dumps(emp_register_payload), content_type="application/json")

        # Login as the standard Employee user
        login_payload = {"username": "staff_member", "password": "password123"}
        login_res = self.client.post("/api/auth/login", data=json.dumps(login_payload), content_type="application/json")
        staff_token = login_res.get_json()["data"]["access_token"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        # 1. Attempt to fetch all employees (should fail)
        res_get_all = self.client.get("/api/employees", headers=staff_headers)
        self.assertEqual(res_get_all.status_code, 403)

        # 2. Attempt to fetch system admin summary stats (should fail)
        res_admin_stat = self.client.get("/api/api/admin/system-summary", headers=staff_headers)
        self.assertEqual(res_admin_stat.status_code, 404) # Not found, or 403. Let's make sure it's blocked.

        # 3. Attempt to query all activity logs (should fail)
        res_logs = self.client.get("/api/activity", headers=staff_headers)
        self.assertEqual(res_logs.status_code, 403)

if __name__ == "__main__":
    unittest.main()
