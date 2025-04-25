import sqlite3
from typing import List, Tuple, Union, Dict
import traceback  # bu juda foydali
from logging import Logger
from utils.log_config import get_logger

def prepare_table(
        db: str, 
        table: str, 
        columns_dict: Dict[str, str], 
        drop: bool = False,
        logger: Logger = None
    ) -> None:
    
    """
    Creates a SQLite table based on the given column definitions.
    If `drop=True`, the existing table will be dropped before creation.

    Args:
        db (str): Path to the SQLite database file (e.g., "my_database.db").
        table (str): Name of the table to be created.
        columns_dict (Dict[str, str]): Dictionary of column names and their data types.
            Example: {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "created_at": "DATETIME"}.
        drop (bool, optional): If True, drops the table if it already exists before creating a new one.
            Default is False.
        logger (Logger, optional): Custom logger instance for logging progress and errors.
            If not provided, a default logger will be created using `get_logger("log", "db.log")`.

    Returns:
        None

    Side Effects:
        - Creates a new table in the SQLite database (or keeps the existing one if `drop` is False).
        - Prints the status of table creation or deletion to the console.

    Example:
        >>> prepare_table(
                db="my.db",
                table="users",
                columns_dict={
                    "id": "INTEGER PRIMARY KEY",
                    "username": "TEXT",
                    "email": "TEXT"
                },
                drop=True
            )
    """


    if logger is None:
        logger = get_logger("db", "app.log")  # fallback if logger not provided

    try:
        with sqlite3.connect(db) as connection:
            cursor = connection.cursor()
            
            if drop:
                cursor.execute("DROP TABLE IF EXISTS %s;"%table)
                
                connection.commit()
                logger.info(f"❌DB: {db}, TABLE: {table} dropped")


            columns_text = ",".join(["%s %s"%(column_name, column_type) for column_name, column_type in columns_dict.items()])
            
            create_table_query = """
                        CREATE TABLE IF NOT EXISTS %(table)s (
                        %(columns_str)s
                        );
                    """%{
                        "table":table,
                        "columns_str": columns_text
                        }
            
            cursor.execute(create_table_query)
            
            connection.commit()
            logger.info(f"✅DB: {db}, TABLE: {table} created")
    except Exception as e:
        logger.log_exception(e, context="preparing tables")

# TESTING prepare_table
# prepare_table(db="test.db", table="test_table", columns_dict={"id": "INTEGER", "data": "TEXT"}, drop=True)


def insert_many(
        db: str, 
        table: str, 
        columns_list: List[str], 
        data: List[Tuple], 
        chunk_size: int = 1000, 
        delete: bool = False, 
        chunk_head: int = 0,
        logger: Logger = None

    ) -> None: 
    
    """
    Inserts data into a SQLite table in chunks.
    Optionally clears the table before inserting new data.

    Args:
        db (str): Path to the SQLite database file (e.g., "my_database.db").
        table (str): Name of the table to insert data into.
        columns_list (List[str]): List of column names, ordered to match each tuple in `data`.
        data (List[Tuple]): Data to insert. Each tuple must match the column order.
        chunk_size (int, optional): Number of rows to insert per chunk. Default is 1000.
        delete (bool, optional): If True, clears the table before inserting. Default is False.
        chunk_head (int, optional): Index of the chunk to start from. Useful for resuming after failure. Default is 0.
        logger (Logger, optional): Custom logger instance for logging progress and errors.
            If not provided, a default logger will be created using `get_logger("log", "db.log")`.

    Returns:
        None

    Side Effects:
        - Inserts rows into the table.
        - Logs each chunk using the provided logger or a fallback logger.
        - Logs or prints errors, but does not stop execution.

    Example:
        >>> insert_many(
                db="my.db",
                table="ads",
                columns_list=["id", "title", "created_at"],
                data=[(1, "Ad1", "2025-04-07"), (2, "Ad2", "2025-04-07")],
                delete=True
            )
    """


    if logger is None:
        logger = get_logger("db", "app.log")  # fallback if logger not provided

    with sqlite3.connect(db) as connection:
        cursor = connection.cursor()

        if delete:
            cursor.execute("DELETE FROM %s;"%table)
            
            connection.commit()
            logger.info(f"❌DB: {db}, TABLE: {table} cleared")


        for i in range(chunk_head, len(data), chunk_size):
            data_chunk = data[i:i + chunk_size]
            
            columns_text = ",".join(columns_list)
            placeholders = ",".join(["?"]*len(columns_list))
            
            try:
                cursor.executemany("""
                    INSERT INTO %(table)s (
                                %(columns)s
                    ) VALUES (%(placeholders)s);
                    """%{
                        "table": table,
                        "columns": columns_text,
                        "placeholders": placeholders
                    }, data_chunk)
                
                connection.commit()
                
                logger.info(f"✅DB: {db}, TABLE: {table} | {len(data)} rows inserted")
            
            except Exception as error:
                logger.log_exception(error, context="inserting rows")


# TESTING insert_many
# insert_many(db="test.db", table="test_table", columns_list=["id", "data"], delete=True, data=[(1, "men"), (2, "sen"), (3, "u")])

def fetch_many(
        db: str,
        table: str,
        columns_list: List[str],
        where: List[Tuple[str, str, str]] = [],
        limit: int = 999_999_999,
        offset: int = 0,
        logger: Logger = None

    ) -> List[Tuple]:
    
    """
    Function to retrieve filtered, column-specific, and optionally limited data from a SQLite database.

    Args:
        db (str): Name or path to the SQLite file.
        table (str): Name of the table.
        columns_list (List[str]): List of columns to retrieve.
        
        where (List[Tuple[str, str, str]], optional): WHERE conditions for filtering.
            Each condition is a tuple:
                - column_name (str): Name of the column, e.g., 'age'
                - operator (str): Comparison operator, e.g., '=', '>', 'LIKE', 'IN', etc.
                - value (str): Value to compare. If type casting is required, use format like '25::INTEGER'.

            Example:
                where = [
                    ('age', '>', '25::INTEGER'),
                    ('is_active', '=', 'true::BOOLEAN'),
                    ('name', 'LIKE', '%Ali%')
                ]

        limit (int, optional): Maximum number of rows to retrieve. Default is 999_999_999.
        offset (int, optional): Number of rows to skip. Default is 0.
        logger (Logger, optional): Custom logger instance for logging progress and errors.
            If not provided, a default logger will be created using `get_logger("log", "db.log")`.

    Returns:
        List[Tuple]: A list of rows retrieved, each row represented as a tuple.
    """


    if logger is None:
        logger = get_logger("db", "app.log")  # fallback if logger not provided
    
    def build_where_clause(where: List[Tuple[str, str, str]]) -> str:
        clauses = []
        for column, operator, value in where:
            if "::" in value or value.upper() == "NULL":
                clause = f"{column} {operator} {value}"
            else:
                clause = f"{column} {operator} '{value}'"
            clauses.append(clause)
        return "WHERE " + " AND ".join(clauses) if clauses else ""

    try:
        with sqlite3.connect(db) as connection:
            cursor = connection.cursor()
            
            columns_text = ", ".join(columns_list)
            where_clause_text = build_where_clause(where)

            query = f"""
                SELECT {columns_text}
                FROM {table}
                {where_clause_text}
                LIMIT {limit}
                OFFSET {offset};
            """

            cursor.execute(query)
            return cursor.fetchall()
    
    except Exception as error:
        logger.log_exception(error, context="fetching rows")
        raise error


def update_row(
        db: str,
        table: str,
        column_with_value: List[Tuple[str, str]],
        where: List[Tuple[str, str, Union[str, List[str]]]] = [],
        logger: Logger = None

    ) -> None:
    """
    A universal function to update rows in a table.
    Supports the IN operator, ::TYPE casting, and AND conditions.

    Args:
        db (str): Path to the SQLite file.
        table (str): Name of the table.
        column_with_value (List[Tuple[str, str]]): Columns to update, given as [(column, value)].
            Example: [("status", "true::BOOLEAN"), ("age", "30")]
        where (List[Tuple[str, str, Union[str, List[str]]]]): Filter conditions, given as [(column, operator, value)].
            Example: [("id", "IN", ["1", "2", "3"]), ("is_active", "=", "true::BOOLEAN")]
        logger (Logger, optional): Custom logger instance for logging progress and errors.
            If not provided, a default logger will be created using `get_logger("log", "db.log")`.

    Returns:
        None
    """

    if logger is None:
        logger = get_logger("db", "app.log")  # fallback if logger not provided

    def format_value(val) -> str:
        if isinstance(val, (int, float, bool)):
            return str(val)  # quote YO‘Q
        if isinstance(val, str):
            return val if "::" in val else f"'{val}'"
        return f"'{str(val)}'"


    def build_set_clause(pairs: List[Tuple[str, str]]) -> str:
        return ", ".join([f"{col} = {format_value(val)}" for col, val in pairs])


    def build_where_clause(conditions: List[Tuple[str, str, Union[str, int, float, bool, List]]]) -> str:
        clauses = []
        for column, operator, value in conditions:
            if operator.upper() == "IN":
                if isinstance(value, list):
                    formatted_values = ", ".join([format_value(v) for v in value])
                else:
                    formatted_values = ", ".join([format_value(v.strip()) for v in str(value).split(",")])
                clause = f"{column} IN ({formatted_values})"
            else:
                clause = f"{column} {operator} {format_value(value)}"
            clauses.append(clause)
        return "WHERE " + " AND ".join(clauses) if clauses else ""


    try:
        with sqlite3.connect(db) as connection:
            cursor = connection.cursor()

            set_clause = build_set_clause(column_with_value)
            where_clause = build_where_clause(where)

            query = f"""
                UPDATE {table}
                SET {set_clause}
                {where_clause};
            """
            logger.info(f"📤 Updating...:\n {query}")
            cursor.execute(query)
            connection.commit()
            logger.info(f"✅ {cursor.rowcount} rows updated.")

    except Exception as error:
        logger.log_exception(error, context="updating rows")
        raise error



# TESTING fetch_many
# data = fetch_many(db="test.db", table="test_table", columns_list=["id", "data"])
# print(data)

