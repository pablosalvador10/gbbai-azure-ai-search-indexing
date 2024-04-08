import logging
import os
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

import pyodbc
from dotenv import load_dotenv

from utils.ml_logging import get_logger

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = get_logger()


class AzureSQLManager:
    def __init__(self, database=None):
        """Initialize the AzureSQLManager with connection parameters from environment variables."""
        self.server = os.getenv("SERVER")
        self.database = database if database else os.getenv("DATABASE")
        self.user_id = os.getenv("USER_ID")
        self.password = os.getenv("PASSWORD")
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establish a connection to the database."""
        if self.database is None:
            raise ValueError("Database cannot be None.")
        self.connection_string = (
            f"DRIVER={{{os.getenv('DB_DRIVER')}}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_UID')};"
            f"PWD={os.getenv('DB_PWD')};"
        )
        try:
            self.conn = pyodbc.connect(self.connection_string, autocommit=True)
            self.cursor = self.conn.cursor()
        except pyodbc.Error as e:
            logging.error(f"Error connecting to Azure SQL Database: {e}")
            raise

    def change_database(self, new_database):
        """Change the current database and reload the connection."""
        self.database = new_database
        self.connect()

    def execute_and_fetch(self, query: str) -> List[Tuple]:
        """
        Execute a given SQL query and return the results.

        :param query: SQL query to be executed.
        :return: List of tuples representing the rows fetched.
        """
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return results
        except pyodbc.Error as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()
            logging.error(
                f"Error executing query: {query}\nError Message: {error_message}\nTraceback: {error_traceback}"
            )
            raise

    def execute(self, query: str):
        """
        Execute a given SQL query without returning the results.

        :param query: SQL query to be executed.
        """
        try:
            self.cursor.execute(query)
        except pyodbc.Error as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()
            logging.error(
                f"Error executing query: {query}\nError Message: {error_message}\nTraceback: {error_traceback}"
            )
            raise

    def fetchall(self) -> List[Tuple]:
        """
        Fetch all rows from the last executed query.

        :return: List of tuples representing the rows fetched.
        """
        try:
            return self.cursor.fetchall()
        except pyodbc.Error as e:
            logging.error("Error fetching all rows: %s", e)
            raise

    def fetchone(self) -> Optional[Tuple]:
        """
        Fetch the next row from the last executed query.

        :return: A tuple representing the next row or None if no more rows are available.
        """
        try:
            return self.cursor.fetchone()
        except pyodbc.Error as e:
            logging.error("Error fetching one row: %s", e)
            raise

    def get_table_names(self) -> List[str]:
        """
        Retrieves the names of all tables in the current database.

        :return: A list of strings containing the names of all tables.
        """
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        try:
            self.cursor.execute(query)
            return [row.TABLE_NAME for row in self.cursor.fetchall()]
        except pyodbc.Error as e:
            logging.error("Error retrieving table names: %s", e)
            raise

    def get_schema_for_all_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves the schema for all tables in the current database.

        :return: A dictionary, with table names as keys and a list of columns (with details) as values.
        """
        table_names = self.get_table_names()
        schema_info = {}
        for table in table_names:
            query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """
            try:
                self.cursor.execute(query, (table,))
                columns = [
                    {"column_name": row.COLUMN_NAME, "data_type": row.DATA_TYPE}
                    for row in self.cursor.fetchall()
                ]
                schema_info[table] = columns
            except pyodbc.Error as e:
                logging.error(f"Error retrieving schema for table {table}: {e}")
                raise
        return schema_info

    def get_schema_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Retrieves the schema for a specific table in the current database.

        :param table_name: The name of the table.
        :return: A list of dictionaries, each containing column name and data type.
        """
        query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        try:
            self.cursor.execute(query, (table_name,))
            return [
                {"column_name": row.COLUMN_NAME, "data_type": row.DATA_TYPE}
                for row in self.cursor.fetchall()
            ]
        except pyodbc.Error as e:
            logging.error(f"Error retrieving schema for table {table_name}: {e}")
            raise

    def process_schema(
        self, table_names: Union[str, List[str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Downloads and processes the schema for a given table or a list of tables.

        :param table_names: The name of the table or a list of table names.
        :return: A dictionary with table names as keys and their processed schemas as values.
        """
        if isinstance(table_names, str):
            table_names = [table_names]

        processed_schemas = {}
        for table in table_names:
            schema = self.get_schema_for_table(table)
            processed_schema = []
            for i, column in enumerate(schema):
                processed_schema.append(
                    {
                        "column_number": i,
                        "column_name": column["column_name"],
                        "data_type": column["data_type"],
                    }
                )
            processed_schemas[table] = processed_schema

        return processed_schemas

    def get_and_process_schema_for_all_tables(self) -> Dict[str, Any]:
        """
        Retrieves and processes the schema for all tables in the current database.

        :return: A dictionary, with table names as keys and processed schema information
                 (including column numbers) as values.
        """
        schemas = self.get_schema_for_all_tables()
        processed_schemas = {}
        for table_name, schema in schemas.items():
            processed_schemas[table_name] = self.process_schema(schema)
        return processed_schemas
