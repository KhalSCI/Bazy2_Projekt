"""
Oracle database connection management with connection pooling.
"""

import oracledb
from contextlib import contextmanager
from typing import Optional, Generator
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG, get_connection_string


class ConnectionPool:
    """Singleton connection pool for Oracle database."""

    _instance: Optional['ConnectionPool'] = None
    _pool: Optional[oracledb.ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, min_connections: int = 2, max_connections: int = 10):
        """Initialize the connection pool."""
        if self._pool is None:
            try:
                self._pool = oracledb.create_pool(
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    dsn=get_connection_string(),
                    min=min_connections,
                    max=max_connections,
                    increment=1
                )
            except oracledb.Error as e:
                raise ConnectionError(f"Nie można utworzyć puli połączeń: {e}")

    def get_connection(self) -> oracledb.Connection:
        """Get a connection from the pool."""
        if self._pool is None:
            self.initialize()
        return self._pool.acquire()

    def release_connection(self, connection: oracledb.Connection):
        """Release a connection back to the pool."""
        if self._pool is not None and connection is not None:
            self._pool.release(connection)

    def close(self):
        """Close the connection pool."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None


# Global pool instance
_pool = ConnectionPool()


def get_connection() -> oracledb.Connection:
    """Get a database connection from the pool."""
    return _pool.get_connection()


def release_connection(connection: oracledb.Connection):
    """Release a connection back to the pool."""
    _pool.release_connection(connection)


@contextmanager
def get_db_connection() -> Generator[oracledb.Connection, None, None]:
    """
    Context manager for database connections.
    Automatically acquires and releases connections from the pool.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
    """
    connection = None
    try:
        connection = get_connection()
        yield connection
    finally:
        if connection is not None:
            release_connection(connection)


@contextmanager
def get_db_cursor() -> Generator[oracledb.Cursor, None, None]:
    """
    Context manager for database cursors.
    Automatically manages connection and cursor lifecycle.

    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()


def test_connection() -> tuple[bool, str]:
    """
    Test the database connection.

    Returns:
        Tuple of (success, message)
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            if result and result[0] == 1:
                return True, "Połączenie z bazą danych działa poprawnie"
            return False, "Nieoczekiwana odpowiedź z bazy danych"
    except oracledb.Error as e:
        error_obj, = e.args
        return False, f"Błąd połączenia: {error_obj.message}"
    except Exception as e:
        return False, f"Nieoczekiwany błąd: {str(e)}"


def execute_query(query: str, params: dict = None) -> list:
    """
    Execute a SELECT query and return results.

    Args:
        query: SQL SELECT query
        params: Optional dictionary of bind parameters

    Returns:
        List of tuples with query results
    """
    with get_db_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()


def execute_query_dict(query: str, params: dict = None) -> list[dict]:
    """
    Execute a SELECT query and return results as list of dictionaries.

    Args:
        query: SQL SELECT query
        params: Optional dictionary of bind parameters

    Returns:
        List of dictionaries with column names as keys
    """
    with get_db_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        columns = [col[0].lower() for col in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results


def execute_dml(query: str, params: dict = None, commit: bool = True) -> int:
    """
    Execute a DML statement (INSERT, UPDATE, DELETE).

    Args:
        query: SQL DML statement
        params: Optional dictionary of bind parameters
        commit: Whether to commit the transaction

    Returns:
        Number of affected rows
    """
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rowcount = cursor.rowcount
            if commit:
                connection.commit()
            return rowcount
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def call_procedure(proc_name: str, params: list = None) -> list:
    """
    Call a stored procedure.

    Args:
        proc_name: Name of the procedure (e.g., 'pkg_gielda.procedure_name')
        params: List of parameters (use cursor.var() for OUT parameters)

    Returns:
        List of output parameter values
    """
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            if params:
                cursor.callproc(proc_name, params)
            else:
                cursor.callproc(proc_name)
            connection.commit()
            return params
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def call_function(func_name: str, return_type, params: list = None):
    """
    Call a stored function.

    Args:
        func_name: Name of the function (e.g., 'pkg_gielda.function_name')
        return_type: Oracle type for return value (e.g., oracledb.NUMBER)
        params: List of input parameters

    Returns:
        Function return value
    """
    with get_db_cursor() as cursor:
        if params:
            return cursor.callfunc(func_name, return_type, params)
        else:
            return cursor.callfunc(func_name, return_type)
