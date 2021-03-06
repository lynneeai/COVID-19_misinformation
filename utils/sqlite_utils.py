"""Solve import issue"""
import os
import sys

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import sqlite3
from all_utils import DOT_DICT

"""
Special constraints:
    - primary_key: (col1, col2, ...)
    - foreign_keys: [(col, referred_col)] where referred_col is in TABLENAME(COL) format
"""


class TABLE:
    def __init__(self, table_name, cols_name):
        self.name = table_name
        self.cols = DOT_DICT({x: x for x in cols_name})
        self.cols_list = cols_name
        self.cols_const = dict()
        self.pk = None
        self.fks = []

    def add_constraint(self, col_name, constraint):
        self.cols_const[col_name] = constraint

    def add_primary_key(self, pk):
        self.pk = pk

    def add_foreign_key(self, fk):
        self.fks.append(fk)


def create_table(table_name, cols_constraints_dict, cur, primary_key=None, foreign_keys=[]):
    cols_str = ", ".join([f"{col_name} {constraint}" for col_name, constraint in cols_constraints_dict.items()])
    if primary_key is not None:
        cols_str += ", PRIMARY KEY("
        cols_str += ", ".join(f"{col}" for col in primary_key)
        cols_str += ")"
    if foreign_keys:
        for fk in foreign_keys:
            col, referred_col = fk[0], fk[1]
            cols_str += f", FOREIGN KEY({col}) REFERENCES {referred_col}"
    stmt = f"CREATE TABLE if not exists {table_name} ({cols_str});"
    print(stmt)
    cur.execute(stmt)


def insert(table_name, values, cur):
    values_str = []
    for v in values:
        if type(v) == str:
            v.replace('"', "'")
            v = f'"{v}"'
        else:
            v = str(v)
        values_str.append(v)
    values_str = ", ".join(values_str)
    stmt = f"INSERT INTO {table_name} VALUES ({values_str});"
    cur.execute(stmt)


def batch_insert(table_name, cols, values, cur):
    cols_str = ", ".join(cols)
    cols_placeholder = ", ".join(["?" for i in range(len(cols))])
    stmt = f"INSERT INTO {table_name} ({cols_str}) VALUES ({cols_placeholder});"
    cur.executemany(stmt, values)


def count_existing_rows(table_name, primary_key_col, cur):
    stmt = f"SELECT {primary_key_col} FROM {table_name};"
    cur.execute(stmt)
    result = len(cur.fetchall())
    return result


def is_row_exists(table_name, cols_vals_dict, cur):
    where_stmt = " AND ".join([f"{col_name}='{col_val}'" for col_name, col_val in cols_vals_dict.items()])
    stmt = f"SELECT COUNT(*) FROM {table_name} WHERE {where_stmt};"
    cur.execute(stmt)
    result = cur.fetchone()[0]
    return result != 0


def update_row(table_name, id_col, cols, values, cur):
    set_stmt = ", ".join([f"{col_name}=?" for col_name in cols])
    where_stmt = f"{id_col}=?"
    stmt = f"""UPDATE {table_name}
                SET {set_stmt}
                WHERE {where_stmt};"""
    try:
        cur.executemany(stmt, values)
    except:
        print(stmt)


def add_column(table_name, col_name, col_type, cur):
    columns = [i[1] for i in cur.execute("PRAGMA table_info(retweets)")]
    if col_name not in columns:
        stmt = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"
        cur.execute(stmt)


def update_table_name(old_table_name, new_table_name, cur):
    sanity_check_stmt = f'SELECT name FROM sqlite_master WHERE type="table" AND name="{old_table_name}";'
    cur.execute(sanity_check_stmt)
    result = cur.fetchone()
    if old_table_name != new_table_name and result:
        stmt = f"ALTER TABLE {old_table_name} RENAME TO {new_table_name};"
        cur.execute(stmt)


def drop_table(table_name, cur):
    stmt = f"DROP TABLE {table_name};"
    print(stmt)
    cur.execute(stmt)


def clear_table(table_name, cur):
    stmt = f"DELETE FROM {table_name};"
    print(stmt)
    cur.execute(stmt)


def get_columns_values(table_name, selecting_cols, cur, where_stmt=None):
    cols_str = ", ".join(selecting_cols)
    stmt = f"SELECT {cols_str} from {table_name}"
    if where_stmt:
        stmt += f" WHERE {where_stmt}"
    stmt += ";"
    # print(stmt)
    cur.execute(stmt)
    return cur.fetchall()
