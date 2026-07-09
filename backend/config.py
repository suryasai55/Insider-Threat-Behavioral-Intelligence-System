import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-key-12345')
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    
    # Database Configuration
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE')
    
    SQLITE_FALLBACK = os.environ.get('SQLITE_FALLBACK', 'True').lower() in ('true', '1', 't')
    
    # SQLAlchemy configurations
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configurations
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    JWT_ERROR_MESSAGE_KEY = 'message'
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Check if MySQL variables are fully set (ignoring placeholder/default values)
        has_mysql = all([
            self.MYSQL_USER,
            self.MYSQL_PASSWORD,
            self.MYSQL_DATABASE,
            self.MYSQL_USER != 'root' or self.MYSQL_PASSWORD != 'yourpassword'  # Check if they are changed from defaults
        ])
        
        if has_mysql:
            return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        
        if self.SQLITE_FALLBACK:
            base_dir = os.path.abspath(os.path.dirname(__file__))
            return f"sqlite:///{os.path.join(base_dir, 'insider_threat.db')}"
            
        raise ValueError("MySQL Database is not configured, and SQLITE_FALLBACK is disabled.")

# Instantiate config
config_instance = Config()
