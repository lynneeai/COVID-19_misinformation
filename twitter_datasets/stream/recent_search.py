"""Solve import issue"""
import os
import sys

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import sqlite3
import json
import requests
import traceback
import pytz
import math
from datetime import datetime, timedelta
from utils.all_utils import print_dict, write_to_log, program_sleep
from utils.sqlite_utils import TABLE, create_table, clear_table, drop_table, batch_insert
from twitter_datasets.utils.twitter_scraper_utils import recent_search_labs, get_single_tweet_by_id_labs
from twitter_datasets.utils.api_keys import TWITTER_API_KEYS
from twitter_datasets.utils.twitter_auth import BearerTokenAuth

twitter_api_keys = TWITTER_API_KEYS()
consumer_key = twitter_api_keys.consumer_key
consumer_secret = twitter_api_keys.consumer_secret

DB_FILE = f"{current_file_dir}/election_search.db"
CLEAR_TABLE = False
DROP_TABLE = False

SEARCH_QUERY = "#2020election -is:retweet lang:en"
LOGFILE_NAME = "election"

VISITED_REPLIES = set()

"""Tables Configs"""
# -------regular_tweets-------
REGULAR_TWEETS = TABLE("regular_tweets", ["tweet_id", "author_id", "created_at", "text", "expanded_urls", "hashtags_str", "mentions_str", "like_count", "quote_count", "reply_count", "retweet_count"])
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.tweet_id, "TEXT PRIMARY KEY")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.author_id, "TEXT NOT NULL")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.created_at, "TEXT NOT NULL")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.text, "TEXT NOT NULL")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.expanded_urls, "TEXT")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.hashtags_str, "TEXT")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.mentions_str, "TEXT")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.like_count, "INTEGER")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.quote_count, "INTEGER")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.reply_count, "INTEGER")
REGULAR_TWEETS.add_constraint(REGULAR_TWEETS.cols.retweet_count, "INTEGER")
assert len(REGULAR_TWEETS.cols) == len(REGULAR_TWEETS.cols_const)


class RECENT_SEARCH:
    def __init__(self, query, start_time, end_time, bearer_token, db_conn, db_cur):
        self.auth = bearer_token
        self.query = query
        self.start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.end_time = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.next_token = None
        self.db_conn = db_conn
        self.db_cur = db_cur

        self.log_file = f'../logs/recent_search_{LOGFILE_NAME}_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

        write_to_log(self.log_file, f"Started to search from {self.start_time} to {self.end_time} with query {self.query}...")

    def update_start_time(self, start_time):
        self.start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def has_next_batch(self):
        return self.next_token != "Does not exist!"

    def save_next_batch(self):
        # try:
        results = recent_search_labs(self.query, self.start_time, self.end_time, self.next_token, self.auth)
        # except Exception as e:
        # 	write_to_log(self.log_file, f'[ERROR]{datetime.now().strftime("%Y%m%d_%H:%M:%S")}: {e}')
        # 	return

        r_obj_list = results["r_obj_list"]
        self.next_token = results["next_token"]

        for r_obj in r_obj_list:
            # # find original tweet if is reply
            # while r_obj['is_reply'] and r_obj["tweet_id"] not in VISITED_REPLIES:
            # 	try:
            # 		write_to_log(self.log_file, f'Reply tweet! tweet_id: {r_obj["tweet_id"]}. Looking for parent tweet! tweet_id: {r_obj["parent_tweet_id"]}')
            # 		VISITED_REPLIES.add(r_obj["tweet_id"])
            # 		r_obj = get_single_tweet_by_id_labs(r_obj['parent_tweet_id'], self.auth)
            # 	except Exception as e:
            # 		print_dict(r_obj)
            # 		write_to_log(self.log_file, e)
            # 		break
            if not r_obj["is_reply"]:
                try:
                    todb_values = [
                        r_obj["tweet_id"],
                        r_obj["author_id"],
                        r_obj["created_at"],
                        r_obj["text"],
                        r_obj["expanded_urls"],
                        r_obj["hashtags_str"],
                        r_obj["mentions_str"],
                        r_obj["like_count"],
                        r_obj["quote_count"],
                        r_obj["reply_count"],
                        r_obj["retweet_count"],
                    ]
                    batch_insert(REGULAR_TWEETS.name, REGULAR_TWEETS.cols, [todb_values], self.db_cur)
                    self.db_conn.commit()
                    write_to_log(self.log_file, f'Saved to regular_tweets! tweet_id: {r_obj["tweet_id"]}')
                except sqlite3.IntegrityError:
                    print("Tweet already saved!")
                except sqlite3.OperationalError:
                    write_to_log(
                        self.log_file, f'-------[ERROR] Cannot save to regular_tweets! tweet_id: {r_obj["tweet_id"]}-------\n' + f"Tweet values: {str(todb_values)}\n" + f"----------------------------------------------------------------------------------"
                    )

        write_to_log(self.log_file, f'**{datetime.now().strftime("%H:%M:%S")}**Finished one batch! Next next_token: {self.next_token}')


if __name__ == "__main__":

    """db connection"""
    CONN = sqlite3.connect(DB_FILE)
    CUR = CONN.cursor()

    """authorization"""
    BEARER_TOKEN = BearerTokenAuth(consumer_key, consumer_secret)

    try:
        """create tables"""
        if DROP_TABLE:
            for t in [REGULAR_TWEETS]:
                drop_table(t.name, CUR)
                CONN.commit()

        for t in [REGULAR_TWEETS]:
            create_table(table_name=t.name, cols_constraints_dict=t.cols_const, cur=CUR, primary_key=t.pk, foreign_keys=t.fks)
            CONN.commit()

        if CLEAR_TABLE:
            for t in [REGULAR_TWEETS]:
                clear_table(t.name, CUR)
                CONN.commit()

        """recent search"""
        while True:
            checkpoint_timestamp = datetime.now().astimezone(pytz.utc) - timedelta(minutes=1)
            start_time = checkpoint_timestamp - timedelta(days=7) + timedelta(minutes=1)
            rs = RECENT_SEARCH(SEARCH_QUERY, start_time, checkpoint_timestamp, BEARER_TOKEN, CONN, CUR)
            while rs.has_next_batch() and (datetime.now().astimezone(pytz.utc) - checkpoint_timestamp < timedelta(days=1)):
                rs.save_next_batch()
                rs.update_start_time(datetime.now().astimezone(pytz.utc) - timedelta(days=7) + timedelta(minutes=1))

            if datetime.now().astimezone(pytz.utc) - checkpoint_timestamp < timedelta(days=1):
                sleep_time = (checkpoint_timestamp + timedelta(days=1) - datetime.now().astimezone(pytz.utc)).total_seconds()
                program_sleep(math.ceil(sleep_time))

    except:
        print(traceback.format_exc())

    """close db connection"""
    CONN.commit()
    CONN.close()
