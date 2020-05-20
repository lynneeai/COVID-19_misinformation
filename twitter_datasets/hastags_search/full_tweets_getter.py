'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import time
import sqlite3
from datetime import datetime
from tqdm import tqdm
from twitter_datasets.utils.twitter_scraper_utils import get_single_tweet_by_id
from utils.all_utils import write_to_log
from utils.sqlite_utils import get_columns_values

class FULL_TWEETS_GETTER:
	def __init__(self, truncated_table_name):
		DB_FILE = f'{current_file_dir}/hashtags_search.db'
		CONN = sqlite3.connect(DB_FILE)
		CUR = CONN.cursor()

		results = get_columns_values(truncated_table_name, ['tweet_id'], CUR)

		CONN.commit()
		CONN.close()

		self.table_name = truncated_table_name
		self.tweets_id_list = []
		for row in results:
			self.tweets_id_list.append(row[0])
		
		self.next_id_ptr = 0
		self.log_file = f'../logs/{truncated_table_name}_getter_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

	def has_next_batch(self):
		return self.next_id_ptr < len(self.tweets_id_list)

	def next_batch(self):
		if self.next_id_ptr == 0:
			write_to_log(self.log_file, f'-------[{datetime.now().strftime("%H:%M:%S")}] Starting getting full tweets for {self.table_name}-------')

		print(f'Getting next batch for {self.table_name}...')
		limit_exceeded = False
		tweets_todb = []
		images_todb = []
		videos_todb = []
		gifs_todb = []
		externals_todb = []

		trange = tqdm(range(self.next_id_ptr, len(self.tweets_id_list)))
		for idx in trange:
			tweet_id = self.tweets_id_list[idx]
			try:
				obj = get_single_tweet_by_id(tweet_id)
				if obj:
					tweets_todb.append([obj['tweet_id'], obj['full_text'], obj['created_at'], obj['language'], 
									   obj['hashtags_str'], obj['mentions_str'], obj['favorite_count'], obj['retweet_count']])
					for media in obj['all_media_urls']:
						if media['media_type'] == 'photo':
							images_todb.append([tweet_id, media['media_url']])
						elif media['media_type'] == 'video':
							videos_todb.append([tweet_id, media['media_url']])
						elif media['media_type'] == 'animated_gif':
							gifs_todb.append([tweet_id, media['media_url']])
						elif media['media_type'] == 'other':
							externals_todb.append([tweet_id, media['media_url']])

			except Exception as e:
				error_code = str(e).split('}]:')[0]
				error_code = error_code.split('\'code\': ')[1]
				if error_code == '88':
					limit_exceeded = True
					self.next_id_ptr = idx

					write_to_log(self.log_file, f'**[{datetime.now().strftime("%H:%M:%S")}]** Finished {idx} tweets! Next tweet idx: {self.next_id_ptr}')
					trange.close()
					break
				else:
					write_to_log(self.log_file, f'{e}')
			
			except Exception as e:
				write_to_log(self.log_file, f'{e}')
		
		trange.close()
		time.sleep(1)
		if not limit_exceeded:
			self.next_id_ptr = len(self.tweets_id_list)
			write_to_log(self.log_file, f'-------[{datetime.now().strftime("%H:%M:%S")}] Finished getting full tweets for {self.table_name}!-------\n')

		return {'limit_exceeded':limit_exceeded, 'tweets_todb':tweets_todb, 'images':images_todb, 'videos':videos_todb, 
				'gifs':gifs_todb, 'externals':externals_todb}