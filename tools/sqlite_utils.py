import sqlite3

def create_table(table_name, cols_with_constraints_dict, cur):
    cols_str = ', '.join([f'{col_name} {constraint}' for col_name, constraint in cols_with_constraints_dict.items()])
    stmt = f'CREATE TABLE if not exists {table_name} ({cols_str});'
    cur.execute(stmt)

def batch_insert(table_name, cols, values, cur):
    cols_str = ', '.join(cols)
    cols_placeholder = ', '.join(['?' for i in range(len(cols))])
    stmt = f'INSERT INTO {table_name} ({cols_str}) VALUES ({cols_placeholder});'
    cur.executemany(stmt, values)

def count_existing_rows(table_name, primary_key_col, cur):
    stmt = f'SELECT {primary_key_col} FROM {table_name};'
    cur.execute(stmt)
    result = len(cur.fetchall())
    return result

def is_row_exists(table_name, cols_vals_dict, cur):
    where_stmt = ' AND '.join([f'{col_name}=\'{col_val}\'' for col_name, col_val in cols_vals_dict.items()])
    stmt = f'SELECT COUNT(*) FROM {table_name} WHERE {where_stmt};'
    cur.execute(stmt)
    result = cur.fetchone()[0]
    return result != 0

def update_row(table_name, id_val_dict, update_val_dict, cur):
    set_stmt = ', '.join([f'{col_name}=\'{col_val}\'' for col_name, col_val in update_val_dict.items()])
    id_col = id_val_dict.keys()[0]
    where_stmt = f'{id_col}={id_val_dict[id_col]}'
    stmt = f'''UPDATE {table_name}
                SET {set_stmt}
                WHERE {where_stmt}'''

def drop_table(table_name, cur):
    stmt = f'DROP TABLE {table_name};'
    cur.execute(stmt)

def clear_table(table_name, cur):
    stmt = f'DELETE FROM {table_name};'
    cur.execute(stmt)