from datetime import datetime
from database.db import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    activity_type = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    device_name = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    employee = db.relationship('Employee', back_populates='activity_logs')

    def __repr__(self):
        return f"<ActivityLog {self.activity_type} - Employee {self.employee_id} at {self.timestamp}>"

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'ip_address': self.ip_address,
            'device_name': self.device_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
