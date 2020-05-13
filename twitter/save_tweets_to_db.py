'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import sqlite3
import tweepy
from tqdm import tqdm
from twitter_api_key import API_KEY
from twitter_scraper import get_single_tweet_by_id
from covid19_scraper import COVID19_SCRAPER
from utils.sqlite_utils import TABLE, create_table, clear_table, batch_insert

DB_FILE = f'{current_file_dir}/twitter.db'
CLEAR_TABLE = True

'''Tables Configs'''
# -------all_tweets-------
ALL_TWEETS = TABLE('all_tweets', ['tweet_id', 'full_text', 'created_at', 'language', 'hashtags_str', 'favorite_count', 'retweet_count'])
ALL_TWEETS.add_constraint(ALL_TWEETS.cols.tweet_id,       'TEXT PRIMARY KEY')
ALL_TWEETS.add_constraint(ALL_TWEETS.cols.full_text,      'TEXT NOT NULL')
ALL_TWEETS.add_constraint(ALL_TWEETS.cols.created_at,     'TEXT NOT NULL')
ALL_TWEETS.add_constraint(ALL_TWEETS.cols.language,       'TEXT')
ALL_TWEETS.add_constraint(ALL_TWEETS.cols.hashtags_str,   'TEXT')
ALL_TWEETS.add_constraint(ALL_TWEETS.cols.favorite_count, 'INTEGER')
ALL_TWEETS.add_constraint(ALL_TWEETS.cols.retweet_count,  'INTEGER')
assert(len(ALL_TWEETS.cols) == len(ALL_TWEETS.cols_const))

# -------images-------
IMAGES = TABLE('images', ['tweet_id', 'media_url'])
IMAGES.add_constraint(IMAGES.cols.tweet_id,  'TEXT NOT NULL')
IMAGES.add_constraint(IMAGES.cols.media_url, 'TEXT NOT NULL')
IMAGES.add_primary_key((IMAGES.cols.tweet_id, IMAGES.cols.media_url))
IMAGES.add_foreign_key((IMAGES.cols.tweet_id, f'{ALL_TWEETS.name}({ALL_TWEETS.cols.tweet_id})'))
assert(len(IMAGES.cols) == len(IMAGES.cols_const))

# -------videos-------
VIDEOS = TABLE('videos', ['tweet_id', 'media_url'])
VIDEOS.add_constraint(VIDEOS.cols.tweet_id,  'TEXT NOT NULL')
VIDEOS.add_constraint(VIDEOS.cols.media_url, 'TEXT NOT NULL')
VIDEOS.add_primary_key((VIDEOS.cols.tweet_id, VIDEOS.cols.media_url))
VIDEOS.add_foreign_key((VIDEOS.cols.tweet_id, f'{ALL_TWEETS.name}({ALL_TWEETS.cols.tweet_id})'))
assert(len(VIDEOS.cols) == len(VIDEOS.cols_const))

# -------gifs-------
GIFS = TABLE('gifs', ['tweet_id', 'media_url'])
GIFS.add_constraint(GIFS.cols.tweet_id,  'TEXT NOT NULL')
GIFS.add_constraint(GIFS.cols.media_url, 'TEXT NOT NULL')
GIFS.add_primary_key((GIFS.cols.tweet_id, GIFS.cols.media_url))
GIFS.add_foreign_key((GIFS.cols.tweet_id, f'{ALL_TWEETS.name}({ALL_TWEETS.cols.tweet_id})'))
assert(len(GIFS.cols) == len(GIFS.cols_const))

# -------externals-------
EXTERNALS = TABLE('externals', ['tweet_id', 'media_url'])
EXTERNALS.add_constraint(EXTERNALS.cols.tweet_id,  'TEXT NOT NULL')
EXTERNALS.add_constraint(EXTERNALS.cols.media_url, 'TEXT NOT NULL')
EXTERNALS.add_primary_key((EXTERNALS.cols.tweet_id, EXTERNALS.cols.media_url))
EXTERNALS.add_foreign_key((EXTERNALS.cols.tweet_id, f'{ALL_TWEETS.name}({ALL_TWEETS.cols.tweet_id})'))
assert(len(EXTERNALS.cols) == len(EXTERNALS.cols_const))

# -------covid19_tweets-------
COVID19_TWEETS = TABLE('covid19_tweets', ['tweet_id'])
COVID19_TWEETS.add_constraint(COVID19_TWEETS.cols.tweet_id, 'TEXT PRIMARY KEY')
COVID19_TWEETS.add_foreign_key((COVID19_TWEETS.cols.tweet_id, f'{ALL_TWEETS.name}({ALL_TWEETS.cols.tweet_id})'))
assert(len(COVID19_TWEETS.cols) == len(COVID19_TWEETS.cols_const))

# -------2020election_tweets-------
ELECTION_TWEETS = TABLE('election2020_tweets', ['tweet_id'])
ELECTION_TWEETS.add_constraint(ELECTION_TWEETS.cols.tweet_id, 'TEXT PRIMARY KEY')
ELECTION_TWEETS.add_foreign_key((ELECTION_TWEETS.cols.tweet_id, f'{ALL_TWEETS.name}({ALL_TWEETS.cols.tweet_id})'))
assert(len(ELECTION_TWEETS.cols) == len(ELECTION_TWEETS.cols_const))

if __name__ == "__main__":

    '''db connection'''
    CONN = sqlite3.connect(DB_FILE)
    CUR = CONN.cursor()

    '''create tables'''
    for t in [ALL_TWEETS, IMAGES, VIDEOS, GIFS, EXTERNALS, COVID19_TWEETS, ELECTION_TWEETS]:
        create_table(table_name=t.name, cols_constraints_dict=t.cols_const, cur=CUR, primary_key=t.pk, foreign_keys=t.fks)

    if CLEAR_TABLE:
        for t in [ALL_TWEETS, IMAGES, VIDEOS, GIFS, EXTERNALS, COVID19_TWEETS, ELECTION_TWEETS]:
            clear_table(t.name, CUR)

    '''covid19 scraper'''
    covid19_scraper = COVID19_SCRAPER()
    while covid19_scraper.has_next_batch():
        obj = covid19_scraper.next_batch()
        for t in [ALL_TWEETS, IMAGES, VIDEOS, GIFS, EXTERNALS, COVID19_TWEETS]:
            batch_insert(t.name, t.cols_list, obj[t.name], CUR)
            CONN.commit()

    '''close db connection'''
    CONN.commit()
    CONN.close()



