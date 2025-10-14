import psycopg2
from config import Config
import logging

class Database:
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.DB_HOST,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME,
                port=self.config.DB_PORT,
                connect_timeout=60
            )
            self.connection.autocommit = True
            logging.info("Database connected successfully")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logging.info("Database disconnected")
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a database query"""
        try:
            # Check if connection exists and is alive
            if not self.connection:
                if not self.connect():
                    raise Exception("Failed to establish database connection")
            
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                if fetch == 'one':
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                cursor.close()
                return cursor.rowcount
        
        except Exception as e:
            logging.error(f"Query execution failed: {str(e)}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def get_connection(self):
        """Get database connection"""
        if not self.connection:
            self.connect()
        return self.connection

# Global database instance
db = Database()
