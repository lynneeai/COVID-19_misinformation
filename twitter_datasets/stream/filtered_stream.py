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
from datetime import datetime, timedelta
from utils.all_utils import print_dict, write_to_log, program_sleep
from utils.sqlite_utils import TABLE, create_table, clear_table, drop_table, batch_insert
from twitter_datasets.utils.twitter_scraper_utils import get_tweet_details_labs, get_single_tweet_by_id_labs
from twitter_datasets.utils.twitter_api_config import API_CONFIG, BearerTokenAuth

api_config = API_CONFIG()
consumer_key = api_config.consumer_key
consumer_secret = api_config.consumer_secret

DB_FILE = f'{current_file_dir}/election_stream.db'
CLEAR_TABLE = False
DROP_TABLE = False

FILTER_RULES = [{'value':'#2020election has:links lang:en'}]
LOGFILE_NAME = 'election'

'''Tables Configs'''
# -------regular_tweets-------
REGULAR_TWEETS = TABLE('regular_tweets', ['tweet_id', 'author_id', 'created_at', 'text', 
										  'expanded_urls', 'hashtags_str', 'mentions_str', 
										  'like_count', 'quote_count', 'reply_count', 'retweet_count'])
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.tweet_id,       'TEXT PRIMARY KEY')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.author_id,      'TEXT NOT NULL')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.created_at,     'TEXT NOT NULL')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.text,       	  'TEXT NOT NULL')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.expanded_urls,  'TEXT')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.hashtags_str,   'TEXT')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.mentions_str,   'TEXT')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.like_count,     'INTEGER')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.quote_count,    'INTEGER')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.reply_count,    'INTEGER')
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.retweet_count,  'INTEGER')
assert(len(REGULAR_TWEETS.cols) == len(REGULAR_TWEETS.cols_const))

# -------retweets-------
REWEETS = TABLE('reweets', ['tweet_id', 'author_id', 'created_at', 'parent_tweet_id', 'parent_tweet_author_id', 
							'like_count', 'quote_count', 'reply_count', 'retweet_count'])
REWEETS.add_constraint(REWEETS.cols.tweet_id,              'TEXT PRIMARY KEY')
REWEETS.add_constraint(REWEETS.cols.author_id,             'TEXT NOT NULL')
REWEETS.add_constraint(REWEETS.cols.created_at,            'TEXT NOT NULL')
REWEETS.add_constraint(REWEETS.cols.parent_tweet_id,       'TEXT NOT NULL')
REWEETS.add_constraint(REWEETS.cols.parent_tweet_author_id,'TEXT NOT NULL')
REWEETS.add_constraint(REWEETS.cols.like_count,            'INTEGER')
REWEETS.add_constraint(REWEETS.cols.quote_count,           'INTEGER')
REWEETS.add_constraint(REWEETS.cols.reply_count,           'INTEGER')
REWEETS.add_constraint(REWEETS.cols.retweet_count,         'INTEGER')
assert(len(REWEETS.cols) == len(REWEETS.cols_const))

class FILTERED_STREAM:
	def __init__(self, bearer_token, filter_rules, db_conn, db_cur):
		self.stream_url = 'https://api.twitter.com/labs/1/tweets/stream/filter'
		self.rules_url = 'https://api.twitter.com/labs/1/tweets/stream/filter/rules'
		self.auth = bearer_token
		self.filter_rules = filter_rules
		self.db_conn = db_conn
		self.db_cur = db_cur

		self.log_file = f'../logs/filter_stream_{LOGFILE_NAME}_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

	def get_all_rules(self):
		response = requests.get(self.rules_url, auth=self.auth)
		if response.status_code is not 200:
			raise Exception(f"Cannot get rules (HTTP %d): %s" % (response.status_code, response.text))
		print_dict(response.json())
		return response.json()

	def delete_all_rules(self, rules):
		if rules is None or 'data' not in rules:
			return None
		ids = list(map(lambda rule: rule['id'], rules['data']))
		payload = {
			'delete': {
			'ids': ids
			}
		}
		response = requests.post(self.rules_url, auth=self.auth, json=payload)
		print_dict(response.json())
		if response.status_code is not 200:
			raise Exception(f"Cannot delete rules (HTTP %d): %s" % (response.status_code, response.text))

	def set_rules(self):
		if self.filter_rules is None:
			return
		payload = {
			'add': self.filter_rules
		}
		response = requests.post(self.rules_url, auth=self.auth, json=payload)
		print_dict(response.json())
		if response.status_code is not 201:
			raise Exception(f"Cannot create rules (HTTP %d): %s" % (response.status_code, response.text))

	def rules_setup(self):
		print('Get original rules...')
		current_rules = self.get_all_rules()
		print('Delete original rules...')
		self.delete_all_rules(current_rules)
		print('Set new rules...')
		self.set_rules()
		print('Current rules:')
		current_rules = self.get_all_rules()
		write_to_log(self.log_file, f'Streaming with filter rules: {str(current_rules)}...')

	def stream_connect(self):
		response = requests.get(self.stream_url, auth=self.auth, stream=True, 
								params={'tweet.format':'detailed',
										'user.format':'detailed',
										'expansions':'referenced_tweets.id,referenced_tweets.id.author_id'})

		if response.status_code > 201:
			raise Exception(f'{response.status_code}: {response.text}')

		# window_count = 0
		# checkpoint_timestamp = datetime.now()
		for response_line in response.iter_lines():
			if response_line:
				tweet_dict = json.loads(response_line)
				r_obj = get_tweet_details_labs(tweet_dict)

				# find original tweet if is retweet
				while r_obj['is_retweet']:
					try:
						todb_values = [r_obj['tweet_id'], r_obj['author_id'], r_obj['created_at'], r_obj['parent_tweet_id'], r_obj['parent_tweet_author_id'], 
									   r_obj['like_count'], r_obj['quote_count'], r_obj['reply_count'], r_obj['retweet_count']]
						batch_insert(REWEETS.name, REWEETS.cols, [todb_values], self.db_cur)
						self.db_conn.commit()
						write_to_log(self.log_file, f'Saved to retweets! tweet_id: {r_obj["tweet_id"]}. Looking for parent tweet! tweet_id: {r_obj["parent_tweet_id"]}')
						r_obj = get_single_tweet_by_id_labs(r_obj['parent_tweet_id'], self.auth)

					except sqlite3.IntegrityError:
						print('Retweet already saved!')
						break
					except sqlite3.OperationalError:
						write_to_log(self.log_file, f'-------[ERROR] Cannot save to retweets! tweet_id: {r_obj["tweet_id"]}-------\n' +
													f'Tweet values: {str(todb_values)}\n' +
													f'Looking for parent tweet! tweet_id: {r_obj["parent_tweet_id"]}\n'+
													f'----------------------------------------------------------------------------')
						r_obj = get_single_tweet_by_id_labs(r_obj['parent_tweet_id'], self.auth)
					except Exception as e:
						write_to_log(self.log_file, e)
						break
					
				if not r_obj['is_retweet']:
					# find original tweet if is reply
					while r_obj['is_reply']:
						try:
							write_to_log(self.log_file, f'Reply tweet! tweet_id: {r_obj["tweet_id"]}. Looking for parent tweet! tweet_id: {r_obj["parent_tweet_id"]}')
							r_obj = get_single_tweet_by_id_labs(r_obj['parent_tweet_id'], self.auth)
						except Exception as e:
							write_to_log(self.log_file, e)
							break
					
					try:
						todb_values = [r_obj['tweet_id'], r_obj['author_id'], r_obj['created_at'], r_obj['text'], 
									r_obj['expanded_urls'], r_obj['hashtags_str'], r_obj['mentions_str'], 
									r_obj['like_count'], r_obj['quote_count'], r_obj['reply_count'], r_obj['retweet_count']]
						batch_insert(REGULAR_TWEETS.name, REGULAR_TWEETS.cols, [todb_values], self.db_cur)
						self.db_conn.commit()
						write_to_log(self.log_file, f'Saved to regular_tweets! tweet_id: {r_obj["tweet_id"]}')

					except sqlite3.IntegrityError:
						print('Original tweet already saved!')
					except sqlite3.OperationalError:
						write_to_log(self.log_file, f'-------[ERROR] Cannot save to regular_tweets! tweet_id: {r_obj["tweet_id"]}-------\n' +
													f'Tweet values: {str(todb_values)}\n' +
													f'----------------------------------------------------------------------------------')
					except Exception as e:
						write_to_log(self.log_file, e)

				# # maximum 12 tweets per minute to avoid using up quota
				# window_count += 1
				# if window_count >= 12:
				# 	if datetime.now() - checkpoint_timestamp < timedelta(minutes=1):
				# 		program_sleep(60)
				# 	window_count = 0
				# 	checkpoint_timestamp = datetime.now()

				
if __name__ == "__main__":
	
	'''db connection'''
	CONN = sqlite3.connect(DB_FILE)
	CUR = CONN.cursor()

	'''authorization'''
	BEARER_TOKEN = BearerTokenAuth(consumer_key, consumer_secret)

	try:
		'''create tables'''
		if DROP_TABLE:
			for t in [REGULAR_TWEETS, REWEETS]:
				drop_table(t.name, CUR)
				CONN.commit()

		for t in [REGULAR_TWEETS, REWEETS]:
			create_table(table_name=t.name, cols_constraints_dict=t.cols_const, cur=CUR, primary_key=t.pk, foreign_keys=t.fks)
			CONN.commit()

		if CLEAR_TABLE:
			for t in [REGULAR_TWEETS, REWEETS]:
				clear_table(t.name, CUR)
				CONN.commit()

		'''filter stream'''
		fs = FILTERED_STREAM(BEARER_TOKEN, FILTER_RULES, CONN, CUR)
		fs.rules_setup()

		timeout = 0
		while True:
			try:
				fs.stream_connect()
				timeout = 0
			except Exception as e:
				if str(e).startswith('429'):
					program_sleep(2 ** timeout)
					timeout += 1
				else:
					print(e)
	except:
		print(traceback.format_exc())

	'''close db connection'''
	CONN.commit()
	CONN.close()