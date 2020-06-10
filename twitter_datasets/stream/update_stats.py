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
from twitter_datasets.utils.twitter_api_config import API_CONFIG, BearerTokenAuth

api_config = API_CONFIG()
consumer_key = api_config.consumer_key
consumer_secret = api_config.consumer_secret

DB_FILE = f'{current_file_dir}/election_stream.db'
TABLE_NAME = 'regular_tweets'
LOG_FILENAME = 'update_stream_tweets_stats'

class UPDATE_STATS:
	def __init__(self, bearer_token, db_conn, db_cur, table_name, log_filename):
		self.auth = bearer_token
		self.db_conn = db_conn
		self.db_cur = db_cur
		self.table_name = table_name

		results = get_columns_values(self.table_name, ['tweet_id'], self.db_cur)
		self.db_conn.commit()

		self.tweets_id_list = []
		for row in results:
			self.tweets_id_list.append(row[0])
		
		self.next_id_ptr = 0
		self.log_file = f'../logs/{log_filename}_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

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
				values = [r_obj['like_count'], r_obj['quote_count'], r_obj['reply_count'], r_obj['retweet_count'], tweet_id]
				update_row(self.table_name, 'tweet_id', ['like_count', 'quote_count', 'reply_count', 'retweet_count'], [values], self.db_cur)
				self.db_conn.commit()
				write_to_log(self.log_file, f'Updated stats for tweet: {tweet_id}')
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

	us = UPDATE_STATS(BEARER_TOKEN, CONN, CUR, TABLE_NAME, LOG_FILENAME)

	while us.has_next_batch():
		try:
			us.save_next_batch()
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