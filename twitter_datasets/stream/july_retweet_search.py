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
from twitter_datasets.utils.twitter_scraper_utils import premium_search_retweet
from twitter_datasets.utils.api_keys_2 import TWITTER_API_KEYS_DAHLIA
from twitter_datasets.utils.twitter_auth import BearerTokenAuth

twitter_api_keys = TWITTER_API_KEYS_DAHLIA()
consumer_key = twitter_api_keys.consumer_key
consumer_secret = twitter_api_keys.consumer_secret
PRODUCT = twitter_api_keys.product_full
LABEL = twitter_api_keys.label

DB_FILE = f"{current_file_dir}/july_retweet_search.db"
CLEAR_TABLE = False
DROP_TABLE = False

SEARCH_QUERY = "#2020election has:links lang:en"
LOGFILE_NAME = "election"

"""Table configs"""
# -------retweets-------
RETWEETS = TABLE("retweets", ["tweet_id", "author_id", "created_at", "parent_tweet_id", "parent_tweet_author_id", "like_count", "quote_count", "reply_count", "retweet_count", "text"])
RETWEETS.add_constraint(RETWEETS.cols.tweet_id, "TEXT PRIMARY KEY")
RETWEETS.add_constraint(RETWEETS.cols.author_id, "TEXT NOT NULL")
RETWEETS.add_constraint(RETWEETS.cols.created_at, "TEXT NOT NULL")
RETWEETS.add_constraint(RETWEETS.cols.parent_tweet_id, "TEXT NOT NULL")
RETWEETS.add_constraint(RETWEETS.cols.parent_tweet_author_id, "TEXT NOT NULL")
RETWEETS.add_constraint(RETWEETS.cols.like_count, "INTEGER")
RETWEETS.add_constraint(RETWEETS.cols.quote_count, "INTEGER")
RETWEETS.add_constraint(RETWEETS.cols.reply_count, "INTEGER")
RETWEETS.add_constraint(RETWEETS.cols.retweet_count, "INTEGER")
RETWEETS.add_constraint(RETWEETS.cols.text, "TEXT")
assert len(RETWEETS.cols) == len(RETWEETS.cols_const)


class JULY_RETWEET_SEARCH:
    def __init__(self, product, label, query, start_time, end_time, bearer_token, db_conn, db_cur):
        self.auth = bearer_token
        self.product = product
        self.label = label
        self.query = query
        self.start_time = start_time.strftime("%Y%m%d%H%M")
        self.end_time = end_time.strftime("%Y%m%d%H%M")
        self.next_token = None
        self.db_conn = db_conn
        self.db_cur = db_cur

        self.log_file = f'../logs/july_retweet_search_{LOGFILE_NAME}_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

        write_to_log(self.log_file, f"Started to search from {self.start_time} to {self.end_time} with query {self.query}...")

    def has_next_batch(self):
        return self.next_token != "Not existed!"

    def save_next_batch(self):
        # try:
        print("Started new batch!")
        try:
            tweets_details, next_token = premium_search_retweet(product=self.product, label=self.label, query=self.query, from_date=self.start_time, to_date=self.end_time, bearer_token=self.auth, next_token=self.next_token)
        except Exception as e:
            if str(e).startswith("429"):
                raise Exception("Rate limit exceeded!")

        r_obj_list = tweets_details
        self.next_token = next_token

        for r_obj in r_obj_list:
            # save only retweets
            if r_obj["is_retweet"]:
                try:
                    todb_values = [
                        r_obj["tweet_id"],
                        r_obj["author_id"],
                        r_obj["created_at"],
                        r_obj["parent_tweet_id"],
                        r_obj["parent_tweet_author_id"],
                        r_obj["like_count"],
                        r_obj["quote_count"],
                        r_obj["reply_count"],
                        r_obj["retweet_count"],
                        r_obj["text"],
                    ]
                    batch_insert(RETWEETS.name, RETWEETS.cols, [todb_values], self.db_cur)
                    self.db_conn.commit()
                    write_to_log(self.log_file, f'Saved to retweets! tweet_id: {r_obj["tweet_id"]}')
                except sqlite3.IntegrityError:
                    print("Retweet already saved!")

        write_to_log(self.log_file, f"Saved one batch!")
        print("Saved one batch!")


if __name__ == "__main__":

    """db connection"""
    CONN = sqlite3.connect(DB_FILE)
    CUR = CONN.cursor()

    """authorization"""
    BEARER_TOKEN = BearerTokenAuth(consumer_key, consumer_secret)

    try:
        """create tables"""
        if DROP_TABLE:
            for t in [RETWEETS]:
                drop_table(t.name, CUR)
                CONN.commit()

        for t in [RETWEETS]:
            create_table(table_name=t.name, cols_constraints_dict=t.cols_const, cur=CUR, primary_key=t.pk, foreign_keys=t.fks)
            CONN.commit()

        if CLEAR_TABLE:
            for t in [RETWEETS]:
                clear_table(t.name, CUR)
                CONN.commit()

        """recent search"""
        end_time = datetime.strptime("2020-07-02_21:53:20", "%Y-%m-%d_%H:%M:%S")
        start_time = datetime.strptime("2020-07-02_21:00:00", "%Y-%m-%d_%H:%M:%S")
        jrs = JULY_RETWEET_SEARCH(PRODUCT, LABEL, SEARCH_QUERY, start_time, end_time, BEARER_TOKEN, CONN, CUR)
        while jrs.has_next_batch():
            try:
                jrs.save_next_batch()
            except Exception as e:
                if str(e) == "Rate limit exceeded!":
                    program_sleep(60)

    except:
        print(traceback.format_exc())

    """close db connection"""
    CONN.commit()
    CONN.close()
