import pymysql
from config import Config
import logging

class Database:
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=self.config.DB_HOST,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME,
                port=self.config.DB_PORT,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                connect_timeout=60,
                read_timeout=60,
                write_timeout=60
            )
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
            if not self.connection or not self.connection.open:
                if not self.connect():
                    raise Exception("Failed to establish database connection")
            
            # Test connection before executing query
            try:
                self.connection.ping(reconnect=True)
            except:
                if not self.connect():
                    raise Exception("Failed to reconnect to database")
            
            # Ensure connection is not None before creating db_handler
            if not self.connection:
                raise Exception("Database connection is None")
                
            with self.connection.cursor() as db_handler:
                db_handler.execute(query, params)
                
                if fetch:
                    if 'SELECT' in query.upper():
                        return db_handler.fetchall()
                    else:
                        return db_handler.fetchone()
                else:
                    # For INSERT operations, return the last inserted ID
                    if 'INSERT' in query.upper():
                        return db_handler.lastrowid
                    else:
                        return db_handler.rowcount
                    
        except Exception as e:
            logging.error(f"Query execution failed: {str(e)}")
            # Try to reconnect and retry once
            try:
                self.connect()
                with self.connection.cursor() as db_handler:
                    db_handler.execute(query, params)
                    
                    if fetch:
                        if 'SELECT' in query.upper():
                            return db_handler.fetchall()
                        else:
                            return db_handler.fetchone()
                    else:
                        # For INSERT operations, return the last inserted ID
                        if 'INSERT' in query.upper():
                            return db_handler.lastrowid
                        else:
                            return db_handler.rowcount
            except Exception as retry_e:
                logging.error(f"Query retry failed: {str(retry_e)}")
                raise retry_e
    
    def get_connection(self):
        """Get database connection"""
        if not self.connection:
            self.connect()
        return self.connection

# Global database instance
db = Database()
