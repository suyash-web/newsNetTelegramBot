import sqlite3

class SqDB():
    def __init__(self, db_name):
        self.DB_NAME = db_name
        self.conn = sqlite3.connect(self.DB_NAME)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

    def create_table(self, table_name, schema: str):
        if not schema:
            raise ValueError("Schema must be provided")

        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        self.cursor.execute(sql)
        self.conn.commit()

    def insert(self, query: str, data_tuple: tuple):
        self.cursor.execute(query, data_tuple)
        self.conn.commit()

    def delete_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        for table_name in tables:
            if not table_name[0].startswith('sqlite_'):
                self.cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]};")

        self.conn.commit()

    def close(self):
        self.conn.close()
