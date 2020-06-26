'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import sqlite3
import json
import requests
import traceback
from tqdm import tqdm
from datetime import datetime, timedelta
from utils.all_utils import print_dict, write_to_log, program_sleep
from utils.sqlite_utils import TABLE, get_columns_values, update_table_name, add_column, update_row
from twitter_datasets.utils.twitter_scraper_utils import get_single_tweet_by_id_labs
from twitter_datasets.utils.api_keys import TWITTER_API_KEYS
from twitter_datasets.utils.twitter_auth import BearerTokenAuth

twitter_api_keys = TWITTER_API_KEYS()
consumer_key = twitter_api_keys.consumer_key
consumer_secret = twitter_api_keys.consumer_secret

DB_FILE = f'{current_file_dir}/election_stream.db'

# -------retweets-------
RETWEETS = TABLE('retweets', ['tweet_id', 'author_id', 'created_at', 'parent_tweet_id', 'parent_tweet_author_id', 
							  'like_count', 'quote_count', 'reply_count', 'retweet_count', 'text'])

class UPDATE_STREAM_RETWEETS:
	def __init__(self, bearer_token, db_conn, db_cur):
		self.auth = bearer_token
		self.db_conn = db_conn
		self.db_cur = db_cur

		update_table_name('reweets', RETWEETS.name, self.db_cur)
		self.db_conn.commit()

		results = get_columns_values(RETWEETS.name, ['tweet_id'], self.db_cur)
		self.db_conn.commit()

		self.tweets_id_list = []
		for row in results:
			self.tweets_id_list.append(row[0])
		
		self.next_id_ptr = 0
		self.log_file = f'../logs/update_stream_retweets_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

	def add_text_column(self):
		add_column(RETWEETS.name, 'text', 'TEXT', self.db_cur)
		self.db_conn.commit()
		write_to_log(self.log_file, '[TABLE CHANGED] Added column text')

	def has_next_batch(self):
		return self.next_id_ptr < len(self.tweets_id_list)

	def save_next_batch(self):
		if self.next_id_ptr == 0:
			write_to_log(self.log_file, f'-------[{datetime.now().strftime("%H:%M:%S")}] Starting to update retweets-------')

		print(f'Processing next batch...')

		limit_exceeded = False
		trange = tqdm(range(self.next_id_ptr, len(self.tweets_id_list)))
		for idx in trange:
			tweet_id = self.tweets_id_list[idx]
			try:
				r_obj = get_single_tweet_by_id_labs(tweet_id, self.auth)
				values = [r_obj['text'], tweet_id]
				update_row(RETWEETS.name, 'tweet_id', ['text'], [values], self.db_cur)
				self.db_conn.commit()
				write_to_log(self.log_file, f'Updated text for retweet: {tweet_id}')
			except Exception as e:
				error_msg = str(e)
				if error_msg == '[Self Defined]Error in response!':
					pass
				elif error_msg.startswith('429'):
					limit_exceeded = True
					self.next_id_ptr = idx
					write_to_log(self.log_file, f'**[{datetime.now().strftime("%H:%M:%S")}]** Finished {idx} tweets! Next tweet idx: {self.next_id_ptr}')
					trange.close()
					break
				else:
					# print(traceback.format_exc())
					raise Exception('error!')

		write_to_log(self.log_file, f'**{datetime.now().strftime("%H:%M:%S")}**Finished one batch!')

		if limit_exceeded:
			raise Exception('[Self Defined]Limit Exceeded!')
		else:
			self.next_id_ptr = len(self.tweets_id_list)

if __name__ == "__main__":

	'''db connection'''
	CONN = sqlite3.connect(DB_FILE)
	CUR = CONN.cursor()

	'''authorization'''
	BEARER_TOKEN = BearerTokenAuth(consumer_key, consumer_secret)

	usr = UPDATE_STREAM_RETWEETS(BEARER_TOKEN, CONN, CUR)
	usr.add_text_column()

	while usr.has_next_batch():
		try:
			usr.save_next_batch()
		except Exception as e:
			error_msg = str(e)
			if error_msg == '[Self Defined]Limit Exceeded!':
				print('Limite Exceeded!')
				program_sleep(900)
			else:
				print(error_msg)
				break
	
	'''close db connection'''
	CONN.commit()
	CONN.close()

	print('Finished updating!')
