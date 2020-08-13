"""Solve import issue"""
import os
import sys

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import sqlite3
import traceback
from tqdm import tqdm
from datetime import datetime, timedelta
from hashtags_searcher import HASHTAGS_SEARCHER
from utils.sqlite_utils import TABLE, create_table, clear_table, drop_table, batch_insert
from twitter_datasets.utils.api_keys import TWITTER_API_KEYS

DB_FILE = f"{current_file_dir}/hashtags_search.db"
CLEAR_TABLE = False
DROP_TABLE = False
SEARCH_MODE = "full"

"""Tables Configs"""
# -------covid19_truncated-------
COVID19_TRUNCATED = TABLE("covid19_truncated", ["tweet_id", "full_text", "created_at", "language", "hashtags_str", "mentions_str", "favorite_count", "retweet_count"])
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.tweet_id, "TEXT PRIMARY KEY")
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.full_text, "TEXT NOT NULL")
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.created_at, "TEXT NOT NULL")
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.language, "TEXT")
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.hashtags_str, "TEXT")
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.mentions_str, "TEXT")
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.favorite_count, "INTEGER")
COVID19_TRUNCATED.add_constraint(COVID19_TRUNCATED.cols.retweet_count, "INTEGER")
assert len(COVID19_TRUNCATED.cols) == len(COVID19_TRUNCATED.cols_const)

# -------election2020_truncated-------
ELECTION_TRUNCATED = TABLE("election2020_truncated", ["tweet_id", "full_text", "created_at", "language", "hashtags_str", "mentions_str", "favorite_count", "retweet_count"])
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.tweet_id, "TEXT PRIMARY KEY")
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.full_text, "TEXT NOT NULL")
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.created_at, "TEXT NOT NULL")
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.language, "TEXT")
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.hashtags_str, "TEXT")
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.mentions_str, "TEXT")
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.favorite_count, "INTEGER")
ELECTION_TRUNCATED.add_constraint(ELECTION_TRUNCATED.cols.retweet_count, "INTEGER")
assert len(ELECTION_TRUNCATED.cols) == len(ELECTION_TRUNCATED.cols_const)

# -------both_truncated-------
BOTH_TRUNCATED = TABLE("both_truncated", ["tweet_id", "full_text", "created_at", "language", "hashtags_str", "mentions_str", "favorite_count", "retweet_count"])
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.tweet_id, "TEXT PRIMARY KEY")
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.full_text, "TEXT NOT NULL")
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.created_at, "TEXT NOT NULL")
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.language, "TEXT")
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.hashtags_str, "TEXT")
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.mentions_str, "TEXT")
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.favorite_count, "INTEGER")
BOTH_TRUNCATED.add_constraint(BOTH_TRUNCATED.cols.retweet_count, "INTEGER")
assert len(BOTH_TRUNCATED.cols) == len(BOTH_TRUNCATED.cols_const)

if __name__ == "__main__":

    """db connection"""
    CONN = sqlite3.connect(DB_FILE)
    CUR = CONN.cursor()

    try:
        """create tables"""
        if DROP_TABLE:
            for t in [COVID19_TRUNCATED, ELECTION_TRUNCATED, BOTH_TRUNCATED]:
                drop_table(t.name, CUR)
                CONN.commit()

        for t in [COVID19_TRUNCATED, ELECTION_TRUNCATED, BOTH_TRUNCATED]:
            create_table(table_name=t.name, cols_constraints_dict=t.cols_const, cur=CUR, primary_key=t.pk, foreign_keys=t.fks)
            CONN.commit()

        if CLEAR_TABLE:
            for t in [COVID19_TRUNCATED, ELECTION_TRUNCATED, BOTH_TRUNCATED]:
                clear_table(t.name, CUR)
                CONN.commit()

        """match hashtag list with table"""
        table_hashtags_dict = {COVID19_TRUNCATED.name: ["#covid19"], ELECTION_TRUNCATED.name: ["#2020election"], BOTH_TRUNCATED.name: ["#covid19", "#2020election"]}
        twitter_api_keys = TWITTER_API_KEYS()

        if SEARCH_MODE == "30day":
            """30day search"""
            from_date = datetime.today() - timedelta(days=30)
            to_date = datetime.today()
            tweets_per_day = 200

            for t in [COVID19_TRUNCATED, ELECTION_TRUNCATED, BOTH_TRUNCATED]:
                print(f"Start {SEARCH_MODE} search for {t.name}...")
                hashtags = table_hashtags_dict[t.name]
                searcher = HASHTAGS_SEARCHER(product=twitter_api_keys.product_30, label=twitter_api_keys.label, hashtags=hashtags, from_date=from_date, to_date=to_date, tweets_per_day=tweets_per_day)
                while searcher.has_next_batch():
                    obj = searcher.next_batch()
                    try:
                        batch_insert(t.name, t.cols_list, obj, CUR)
                        CONN.commit()
                    except:
                        print(traceback.format_exc())
        elif SEARCH_MODE == "full":
            """fullarchive search"""
            from_date = datetime.today() - timedelta(days=30) - timedelta(days=25)
            to_date = datetime.today() - timedelta(days=30)
            tweets_per_day = 100

            for t in [ELECTION_TRUNCATED, BOTH_TRUNCATED]:
                print(f"Start {SEARCH_MODE} day search for {t.name}...")
                hashtags = table_hashtags_dict[t.name]
                searcher = HASHTAGS_SEARCHER(product=twitter_api_keys.product_full, label=twitter_api_keys.label, hashtags=hashtags, from_date=from_date, to_date=to_date, tweets_per_day=tweets_per_day)
                while searcher.has_next_batch():
                    obj = searcher.next_batch()
                    try:
                        batch_insert(t.name, t.cols_list, obj, CUR)
                        CONN.commit()
                    except:
                        print(traceback.format_exc())

    except:
        print(traceback.format_exc())

    """close db connection"""
    CONN.commit()
    CONN.close()
