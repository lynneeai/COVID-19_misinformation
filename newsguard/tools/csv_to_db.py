import csv
import os
import sqlite3
from datetime_converter import convert_datetime
from sqlite_utils import *

CLEAR_TABLE = True
DB_FILE = '../newsguard_tracked.db'
CSV_ROOT = '../articles'

TABLE_NAME = 'all_articles'
COLS = ['article_id', 'title', 'source', 'content', 'publishedAt', 'url', 'label']
COLS_WITH_CONSTRAINTS = {COLS[0]: 'INTEGER PRIMARY KEY', 
						 COLS[1]: 'TEXT NOT NULL',
						 COLS[2]: 'TEXT NOT NULL',
						 COLS[3]: 'TEXT NOT NULL',
						 COLS[4]: 'TEXT',
						 COLS[5]: 'TEXT NOT NULL',
						 COLS[6]: 'TEXT'}

CONN = sqlite3.connect(DB_FILE)
CUR = CONN.cursor()

create_table(TABLE_NAME, COLS_WITH_CONSTRAINTS, CUR)

if CLEAR_TABLE:
	clear_table(TABLE_NAME, CUR)

csv_files = [item for item in os.listdir(CSV_ROOT) if item.endswith('.csv')]
id_ptr = count_existing_rows(TABLE_NAME, COLS[0], CUR)
print(f'-----Total articles before inserting: {id_ptr}-----')
for csv_file in csv_files:
	print(f'Processing {csv_file}...')
	csv_file = f'{CSV_ROOT}/{csv_file}'
	with open(csv_file, 'r') as infile:
		articles = csv.DictReader(infile)
		to_db = []
		local_ptr = 0
		for item in articles:
			title, content, publishedAt, url = item['title'], item['content'], item['publishedAt'], item['url']
			source = csv_file.split('/')[-1][:-4]
			publishedAt = convert_datetime(publishedAt, source=source)
			if not is_row_exists(TABLE_NAME, {'url': url}, CUR):
				article_id = id_ptr + local_ptr
				label = 'unknown'
				to_db.append([article_id, title, source, content, publishedAt, url, label])
				local_ptr += 1
		
		batch_insert(TABLE_NAME, COLS, to_db, CUR)
		CONN.commit()
		id_ptr += local_ptr
		print(f'{local_ptr} articles inserted!')

print(f'-----Total articles after inserting: {id_ptr}-----')

CONN.commit()
CONN.close()