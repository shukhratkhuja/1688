import sqlite3
from typing import List, Tuple, Union, Dict
import traceback  # bu juda foydali
from logging import Logger
import time
from utils.log_config import get_logger
def prepare_table(
        db: str, 
        table: str, 
        columns_dict: Dict[str, str], 
        drop: bool = False,
        logger: Logger = None
    ) -> bool:
    
    """
    Creates a SQLite table based on the given column definitions.
    
    Args:
        db (str): Path to the SQLite database file.
        table (str): Name of the table to be created.
        columns_dict (Dict[str, str]): Dictionary of column names and their data types.
        drop (bool, optional): If True, drops the table if it already exists.
        logger (Logger, optional): Custom logger instance for logging.
        
    Returns:
        bool: True if table was created successfully, False otherwise
    """
    if logger is None:
        logger = get_logger("db", "app.log")

    # Validate inputs
    if not db or not table or not columns_dict:
        logger.error("Invalid parameters: db, table, and columns_dict must be provided")
        return False
        
    try:
        with sqlite3.connect(db) as connection:
            cursor = connection.cursor()
            
            if drop:
                try:
                    cursor.execute("DROP TABLE IF EXISTS %s;"%table)
                    connection.commit()
                    logger.info(f"❌DB: {db}, TABLE: {table} dropped")
                except sqlite3.OperationalError as e:
                    logger.error(f"Failed to drop table {table}: {str(e)}")
                    raise

            # Build columns string with validation
            try:
                columns_text = ",".join(["%s %s"%(column_name, column_type) 
                                       for column_name, column_type in columns_dict.items()])
            except Exception as e:
                logger.error(f"Failed to build columns string: {str(e)}")
                raise
                
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table} (
                {columns_text}
                );
            """
            
            cursor.execute(create_table_query)
            connection.commit()
            logger.info(f"✅DB: {db}, TABLE: {table} created")
            return True
            
    except sqlite3.OperationalError as e:
        # Database might be locked or other operational issue
        logger.error(f"SQLite operational error while creating table {table}: {str(e)}")
        raise
    except sqlite3.DatabaseError as e:
        # More general database error
        logger.error(f"Database error while creating table {table}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating table {table}: {str(e)}")
        logger.log_exception(e, context="preparing tables")
        raise
    finally:
        cursor.close()
        connection.close()
        
    return False

def insert_many(
        db: str, 
        table: str, 
        columns_list: List[str], 
        data: List[Tuple], 
        chunk_size: int = 1000, 
        delete: bool = False, 
        chunk_head: int = 0,
        logger: Logger = None,
        max_retries: int = 3
    ) -> bool:
    
    """
    Inserts data into a SQLite table in chunks with retry logic.
    
    Args:
        db (str): Path to the SQLite database file.
        table (str): Name of the table to insert data into.
        columns_list (List[str]): List of column names.
        data (List[Tuple]): Data to insert. Each tuple must match the column order.
        chunk_size (int, optional): Number of rows to insert per chunk.
        delete (bool, optional): If True, clears the table before inserting.
        chunk_head (int, optional): Index of the chunk to start from.
        logger (Logger, optional): Custom logger instance.
        max_retries (int, optional): Maximum number of retry attempts for transient errors.
        
    Returns:
        bool: True if all data was inserted successfully, False otherwise
    """
    if logger is None:
        logger = get_logger("db", "app.log")
        
    # Validate inputs
    if not db or not table or not columns_list:
        logger.error("Invalid parameters: db, table, and columns_list must be provided")
        return False
        
    if not data:
        logger.warning(f"No data provided to insert into {table}")
        return True  # Nothing to do, but not an error

    try:
        with sqlite3.connect(db) as connection:
            cursor = connection.cursor()

            if delete:
                try:
                    cursor.execute(f"DELETE FROM {table};")
                    connection.commit()
                    logger.info(f"❌DB: {db}, TABLE: {table} cleared")
                except sqlite3.Error as e:
                    logger.error(f"Failed to clear table {table}: {str(e)}")
                    raise

            # Process data in chunks
            for i in range(chunk_head, len(data), chunk_size):
                data_chunk = data[i:i + chunk_size]
                
                columns_text = ",".join(columns_list)
                placeholders = ",".join(["?"]*len(columns_list))
                
                insert_query = f"""
                    INSERT INTO {table} (
                                {columns_text}
                    ) VALUES ({placeholders});
                """
                
                # Implement retry logic for transient errors
                retries = 0
                while retries <= max_retries:
                    try:
                        cursor.executemany(insert_query, data_chunk)
                        connection.commit()
                        logger.info(f"✅DB: {db}, TABLE: {table} | {len(data_chunk)} rows inserted")
                        break
                    except sqlite3.OperationalError as e:
                        retries += 1
                        if "database is locked" in str(e) and retries <= max_retries:
                            wait_time = 0.5 * (2 ** retries)  # Exponential backoff
                            logger.warning(f"Database locked, retry {retries}/{max_retries} after {wait_time}s")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"SQLite operational error: {str(e)}")
                            raise
                    except Exception as error:
                        logger.error(f"Error inserting data chunk: {str(error)}")
                        raise
                        
                if retries > max_retries:
                    logger.error(f"Failed to insert chunk after {max_retries} retries")
                    return False
                    
            return True
                
    except Exception as error:
        logger.log_exception(error, context="inserting rows")
        raise

    finally:
        cursor.close()
        connection.close()
        
    return False
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
    finally:
        cursor.close()
        connection.close()


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

            query = """
                UPDATE %s
                SET %s
                %s;
            """ % (table, set_clause, where_clause)
            logger.info(f"📤 Updating...:\n {query}")
            cursor.execute(query)
            connection.commit()
            logger.info(f"✅ {cursor.rowcount} rows updated.")

        
    except Exception as error:
        logger.log_exception(error, context="updating rows")
        raise error
    
    finally:
        cursor.close()
        connection.close()


# TESTING fetch_many
# data = fetch_many(db="test.db", table="test_table", columns_list=["id", "data"])
# print(data)
