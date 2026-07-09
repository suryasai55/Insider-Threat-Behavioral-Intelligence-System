import re
from marshmallow import Schema, fields, validate, ValidationError

# Regex for phone numbers: fits general formats +1234567890, 123-456-7890, etc.
PHONE_REGEX = re.compile(r'^\+?[1-9]\d{1,14}$|^(\d{3}-\d{3}-\d{4})$|^\d{10}$')

def validate_phone(value):
    if value and not PHONE_REGEX.match(value):
        raise ValidationError("Invalid phone number format. Must be numeric or standard format like +1234567890 or 123-456-7890.")

class LoginSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=100))

class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=100))
    role_name = fields.Str(required=False, validate=validate.OneOf(['ADMINISTRATOR', 'ADMIN', 'SECURITY_ANALYST', 'SOC_ENGINEER', 'SECURITY_MANAGER', 'EMPLOYEE']), dump_default='EMPLOYEE')
    
    # Optional linked Employee details on register
    employee_code = fields.Str(required=False, validate=validate.Length(max=50))
    first_name = fields.Str(required=False, validate=validate.Length(max=100))
    last_name = fields.Str(required=False, validate=validate.Length(max=100))
    email = fields.Email(required=False)
    phone = fields.Str(required=False, validate=validate_phone)
    department = fields.Str(required=False, validate=validate.Length(max=100))
    designation = fields.Str(required=False, validate=validate.Length(max=100))
    joining_date = fields.Date(required=False)

class EmployeeSchema(Schema):
    employee_code = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    phone = fields.Str(required=False, validate=validate_phone, allow_none=True)
    department = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    designation = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    joining_date = fields.Date(required=True)
    status = fields.Str(required=False, validate=validate.OneOf(['ACTIVE', 'INACTIVE', 'SUSPENDED']), dump_default='ACTIVE')
