"""Solve import issue"""
import os
import sys

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import csv
import sqlite3
from datetime_converter import convert_datetime
from utils.sqlite_utils import create_table, batch_insert, count_existing_rows, is_row_exists, clear_table

CLEAR_TABLE = True
DB_FILE = "../newsguard_tracked.db"
CSV_ROOT = "../articles"

TABLE_NAME = "all_articles"
COLS = ["article_id", "title", "source", "content", "publishedAt", "url", "label"]
COLS_WITH_CONSTRAINTS = {COLS[0]: "INTEGER PRIMARY KEY", COLS[1]: "TEXT NOT NULL", COLS[2]: "TEXT NOT NULL", COLS[3]: "TEXT NOT NULL", COLS[4]: "TEXT", COLS[5]: "TEXT NOT NULL", COLS[6]: "TEXT"}

CONN = sqlite3.connect(DB_FILE)
CUR = CONN.cursor()

create_table(table_name=TABLE_NAME, cols_constraints_dict=COLS_WITH_CONSTRAINTS, cur=CUR)
CONN.commit()

if CLEAR_TABLE:
    clear_table(TABLE_NAME, CUR)
    CONN.commit()

csv_files = [item for item in os.listdir(CSV_ROOT) if item.endswith(".csv")]
id_ptr = count_existing_rows(TABLE_NAME, COLS[0], CUR)
print(f"-----Total articles before inserting: {id_ptr}-----")
for csv_file in csv_files:
    print(f"Processing {csv_file}...")
    csv_file = f"{CSV_ROOT}/{csv_file}"
    with open(csv_file, "r") as infile:
        articles = csv.DictReader(infile)
        to_db = []
        local_ptr = 0
        for item in articles:
            title, content, publishedAt, url = item["title"], item["content"], item["publishedAt"], item["url"]
            source = csv_file.split("/")[-1][:-4]
            publishedAt = convert_datetime(publishedAt, source=source)
            if not is_row_exists(TABLE_NAME, {"url": url}, CUR):
                article_id = id_ptr + local_ptr
                label = "unknown"
                to_db.append([article_id, title, source, content, publishedAt, url, label])
                local_ptr += 1

        batch_insert(TABLE_NAME, COLS, to_db, CUR)
        CONN.commit()
        id_ptr += local_ptr
        print(f"{local_ptr} articles inserted!")

print(f"-----Total articles after inserting: {id_ptr}-----")

CONN.commit()
CONN.close()
