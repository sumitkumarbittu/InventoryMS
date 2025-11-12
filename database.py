import psycopg2
import psycopg2.extras as pg_extras
from config import Config
import logging
import os
import re
from decimal import Decimal

class Database:
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            dsn = getattr(self.config, 'DATABASE_URL', None)
            if not dsn:
                raise ValueError("DATABASE_URL is not set")
            # Normalize common Heroku-style URL prefix
            if dsn.startswith('postgres://'):
                dsn = dsn.replace('postgres://', 'postgresql://', 1)
            self.connection = psycopg2.connect(dsn, connect_timeout=60, cursor_factory=pg_extras.RealDictCursor)
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
                    result = self._normalize_row(result)
                else:
                    result = cursor.fetchall()
                    result = [self._normalize_row(r) for r in result]
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

    def _transform_schema_sql(self, sql: str) -> str:
        """Transform MySQL-ish SQL to PostgreSQL-compatible and make it idempotent."""
        # Drop psql/meta commands like \c and MySQL USE
        sql = re.sub(r"(?m)^\\s*\\\\c\\s+.*$", "", sql)  # remove lines starting with \c
        sql = re.sub(r"(?mi)^\\s*USE\\s+.+?;\\s*$", "", sql)

        # Remove inline comments? Keep standard comments; they won't break execution when we split.

        # AUTO_INCREMENT -> SERIAL
        sql = re.sub(r"(?i)\bINT\s+PRIMARY\s+KEY\s+AUTO_INCREMENT\b", "SERIAL PRIMARY KEY", sql)
        sql = re.sub(r"(?i)\bINT\s+AUTO_INCREMENT\b", "SERIAL", sql)

        # ENUM(...) -> TEXT
        sql = re.sub(r"(?i)ENUM\s*\([^\)]*\)", "TEXT", sql)

        # UNIQUE KEY name (cols) -> UNIQUE (cols)
        sql = re.sub(r"(?i)UNIQUE\s+KEY\s+\w+\s*\(([^\)]+)\)", r"UNIQUE (\1)", sql)

        # Remove ON UPDATE CURRENT_TIMESTAMP (not needed in PG without trigger)
        sql = re.sub(r"(?i)\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP", "", sql)

        # CREATE TABLE -> CREATE TABLE IF NOT EXISTS
        sql = re.sub(r"(?i)CREATE\s+TABLE\s+", "CREATE TABLE IF NOT EXISTS ", sql)

        # CREATE INDEX -> CREATE INDEX IF NOT EXISTS
        sql = re.sub(r"(?i)CREATE\s+INDEX\s+", "CREATE INDEX IF NOT EXISTS ", sql)

        # CREATE VIEW -> CREATE OR REPLACE VIEW
        sql = re.sub(r"(?i)CREATE\s+VIEW\s+", "CREATE OR REPLACE VIEW ", sql)

        return sql

    def _split_sql_statements(self, sql: str):
        """Split SQL string into individual statements by semicolon.
        This is a simple splitter suitable for our schema file.
        """
        statements = []
        buff = []
        in_string = False
        quote_char = ''
        for ch in sql:
            if ch in ("'", '"'):
                if not in_string:
                    in_string = True
                    quote_char = ch
                elif quote_char == ch:
                    in_string = False
            if ch == ';' and not in_string:
                stmt = ''.join(buff).strip()
                if stmt:
                    statements.append(stmt)
                buff = []
            else:
                buff.append(ch)
        # last statement
        tail = ''.join(buff).strip()
        if tail:
            statements.append(tail)
        return statements

    def initialize_schema(self, schema_file_path: str = 'database_schema.sql'):
        """Ensure database schema exists and seed sample data if tables are empty.
        This runs on every app start and is idempotent.
        """
        try:
            # Ensure connection
            if not self.connection:
                self.connect()

            # Resolve schema path
            path = schema_file_path
            if not os.path.isabs(path):
                path = os.path.join(os.path.dirname(os.path.abspath(__file__)), schema_file_path)
            if not os.path.exists(path):
                logging.warning(f"Schema file not found: {path}")
                return

            with open(path, 'r', encoding='utf-8') as f:
                raw_sql = f.read()

            transformed = self._transform_schema_sql(raw_sql)
            statements = self._split_sql_statements(transformed)

            ddl_statements = []
            insert_statements = []
            for stmt in statements:
                head = stmt.strip().split()[0].upper() if stmt.strip() else ''
                if head == 'INSERT':
                    insert_statements.append(stmt)
                else:
                    ddl_statements.append(stmt)

            # Apply DDL statements idempotently
            for stmt in ddl_statements:
                try:
                    self.execute_query(stmt)
                except Exception as e:
                    logging.warning(f"Schema DDL statement failed (continuing): {e}\nStatement: {stmt[:200]}...")

            # Seed sample data per table only if the table is empty
            if insert_statements:
                seed_pairs = []  # list of (table, stmt) preserving order
                for stmt in insert_statements:
                    m = re.search(r"(?i)INSERT\s+INTO\s+(\w+)", stmt)
                    table = m.group(1) if m else None
                    seed_pairs.append((table, stmt))

                empties = {}
                for table, _ in seed_pairs:
                    if not table or table in empties:
                        continue
                    try:
                        count_row = self.execute_query(f"SELECT COUNT(*) FROM {table}", fetch='one')
                        empties[table] = (count_row[0] if count_row else 0) == 0
                    except Exception:
                        empties[table] = False

                for table, stmt in seed_pairs:
                    if table and empties.get(table):
                        try:
                            self.execute_query(stmt)
                        except Exception as e:
                            logging.warning(f"Seed insert failed (continuing): {e}\nStatement: {stmt[:200]}...")

            logging.info("Database schema initialization completed")
        except Exception as e:
            logging.error(f"Schema initialization failed: {e}")
            # Do not raise to avoid crashing app start

    def _normalize_row(self, row):
        """Convert psycopg2 RealDictRow (and Decimal values) to JSON-serializable types."""
        if row is None:
            return None
        if isinstance(row, dict):
            return {k: self._normalize_value(v) for k, v in row.items()}
        return row

    def _normalize_value(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value

# Global database instance
db = Database()
