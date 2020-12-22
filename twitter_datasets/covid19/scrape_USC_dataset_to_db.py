"""Solve import issue"""
import os
import sys

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import sqlite3
import tweepy
import traceback
from tqdm import tqdm
from usc_scraper import USC_SCRAPER
from utils.sqlite_utils import (
    TABLE,
    create_table,
    clear_table,
    drop_table,
    batch_insert,
)
from utils.all_utils import program_sleep

DB_FILE = f"{current_file_dir}/usc_twitter.db"
CLEAR_TABLE = False
DROP_TABLE = False

"""Tables Configs"""
# -------covid19_tweets-------
COVID19_TWEETS = TABLE(
    "covid19_tweets",
    [
        "tweet_id",
        "full_text",
        "created_at",
        "language",
        "hashtags_str",
        "mentions_str",
        "favorite_count",
        "retweet_count",
    ],
)
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.tweet_id, "TEXT PRIMARY KEY")
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.full_text, "TEXT NOT NULL")
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.created_at, "TEXT NOT NULL")
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.language, "TEXT")
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.hashtags_str, "TEXT")
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.mentions_str, "TEXT")
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.favorite_count, "INTEGER")
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.retweet_count, "INTEGER")
assert len(COVID19_TWEETS.cols) == len(COVID19_TWEETS.cols_const)

# -------images-------
IMAGES = TABLE("images", ["tweet_id", "media_url"])
IMAGES.add_constraint(IMAGES.cols.tweet_id, "TEXT NOT NULL")
IMAGES.add_constraint(IMAGES.cols.media_url, "TEXT NOT NULL")
IMAGES.add_primary_key((IMAGES.cols.tweet_id, IMAGES.cols.media_url))
IMAGES.add_foreign_key(
    (IMAGES.cols.tweet_id, f"{COVID19_TWEETS.name}({COVID19_TWEETS.cols.tweet_id})")
)
assert len(IMAGES.cols) == len(IMAGES.cols_const)

# -------videos-------
VIDEOS = TABLE("videos", ["tweet_id", "media_url"])
VIDEOS.add_constraint(VIDEOS.cols.tweet_id, "TEXT NOT NULL")
VIDEOS.add_constraint(VIDEOS.cols.media_url, "TEXT NOT NULL")
VIDEOS.add_primary_key((VIDEOS.cols.tweet_id, VIDEOS.cols.media_url))
VIDEOS.add_foreign_key(
    (VIDEOS.cols.tweet_id, f"{COVID19_TWEETS.name}({COVID19_TWEETS.cols.tweet_id})")
)
assert len(VIDEOS.cols) == len(VIDEOS.cols_const)

# -------gifs-------
GIFS = TABLE("gifs", ["tweet_id", "media_url"])
GIFS.add_constraint(GIFS.cols.tweet_id, "TEXT NOT NULL")
GIFS.add_constraint(GIFS.cols.media_url, "TEXT NOT NULL")
GIFS.add_primary_key((GIFS.cols.tweet_id, GIFS.cols.media_url))
GIFS.add_foreign_key(
    (GIFS.cols.tweet_id, f"{COVID19_TWEETS.name}({COVID19_TWEETS.cols.tweet_id})")
)
assert len(GIFS.cols) == len(GIFS.cols_const)

# -------externals-------
EXTERNALS = TABLE("externals", ["tweet_id", "media_url"])
EXTERNALS.add_constraint(EXTERNALS.cols.tweet_id, "TEXT NOT NULL")
EXTERNALS.add_constraint(EXTERNALS.cols.media_url, "TEXT NOT NULL")
EXTERNALS.add_primary_key((EXTERNALS.cols.tweet_id, EXTERNALS.cols.media_url))
EXTERNALS.add_foreign_key(
    (EXTERNALS.cols.tweet_id, f"{COVID19_TWEETS.name}({COVID19_TWEETS.cols.tweet_id})")
)
assert len(EXTERNALS.cols) == len(EXTERNALS.cols_const)

# -------election2020_tweets-------
ELECTION_TWEETS = TABLE("election2020_tweets", ["tweet_id"])
ELECTION_TWEETS.add_constraint(ELECTION_TWEETS.cols.tweet_id, "TEXT PRIMARY KEY")
ELECTION_TWEETS.add_foreign_key(
    (
        ELECTION_TWEETS.cols.tweet_id,
        f"{COVID19_TWEETS.name}({COVID19_TWEETS.cols.tweet_id})",
    )
)
assert len(ELECTION_TWEETS.cols) == len(ELECTION_TWEETS.cols_const)

if __name__ == "__main__":

    """db connection"""
    CONN = sqlite3.connect(DB_FILE)
    CUR = CONN.cursor()

    try:
        """create tables"""
        if DROP_TABLE:
            for t in [COVID19_TWEETS, IMAGES, VIDEOS, GIFS, EXTERNALS, ELECTION_TWEETS]:
                drop_table(t.name, CUR)
                CONN.commit()

        for t in [COVID19_TWEETS, IMAGES, VIDEOS, GIFS, EXTERNALS, ELECTION_TWEETS]:
            create_table(
                table_name=t.name,
                cols_constraints_dict=t.cols_const,
                cur=CUR,
                primary_key=t.pk,
                foreign_keys=t.fks,
            )
            CONN.commit()

        if CLEAR_TABLE:
            for t in [COVID19_TWEETS, IMAGES, VIDEOS, GIFS, EXTERNALS, ELECTION_TWEETS]:
                clear_table(t.name, CUR)
                CONN.commit()

        """covid19 scraper"""
        usc_scraper = USC_SCRAPER()
        while usc_scraper.has_next_batch():
            obj = usc_scraper.next_batch()
            for t in [COVID19_TWEETS, IMAGES, VIDEOS, GIFS, EXTERNALS]:
                try:
                    batch_insert(t.name, t.cols_list, obj[t.name], CUR)
                    CONN.commit()
                except Exception as e:
                    print(e)

            if obj["limit_exceeded"]:
                print("Rate limit exceeded!")
                program_sleep(900)

    except:
        print(traceback.format_exc())

    """close db connection"""
    CONN.commit()
    CONN.close()
