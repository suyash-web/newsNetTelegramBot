import sqlite3

class SqDB():
    def __init__(self, db_name):
        self.DB_NAME = db_name
        self.conn = sqlite3.connect(self.DB_NAME)
        self.conn.row_factory = sqlite3.Row
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
    
    def get_latest_entry_from_table(self, table_name, param_name=None, value=None):
        with SqDB(self.DB_NAME) as db:
            if param_name is None and value is None:
                db.cursor.execute(f"""
                    SELECT * FROM {table_name}
                    ORDER BY rowid DESC
                    LIMIT 1
                """)
            elif (param_name is None) ^ (value is None):
                raise ValueError("If you provide 'param_name', you must also provide 'value' (and vice versa).")
            else:
                db.cursor.execute(f"""
                    SELECT * FROM {table_name}
                    WHERE {param_name} = ?
                    ORDER BY rowid DESC
                    LIMIT 1
                """, (value,))
            row = db.cursor.fetchone()
            if row:
                return dict(row)
            else:
                raise ValueError("Data nor found. Please check your params.")

    def get_all_data_from_table(self, table_name):
        with SqDB(self.DB_NAME) as db:
            db.cursor.execute(f"SELECT * FROM {table_name}")
            data = db.cursor.fetchall()
        return [dict(row) for row in data]

    def delete_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        for table_name in tables:
            if not table_name[0].startswith('sqlite_'):
                self.cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]};")

        self.conn.commit()

    def delete_row(self, param, val):
        self.cursor.execute(f"DELETE FROM my_table WHERE {param} = ?", (val,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def close(self):
        self.conn.close()
