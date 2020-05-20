'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import time
import sqlite3
import itertools
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from nltk import FreqDist
from datetime import datetime
from tqdm import tqdm
from twitter_datasets.utils.tweets_utils import tweet_toks
from utils.sqlite_utils import get_columns_values

DB_FILE = f'{current_file_dir}/election2020_full.db'
MOST_COMMON = 20
CONN = sqlite3.connect(DB_FILE)
CUR = CONN.cursor()

results = get_columns_values('election2020_tweets', ['full_text', 'hashtags_str', 'mentions_str'], CUR)

CONN.commit()
CONN.close()

tweets_list = []
hashtags_list = []
mentions_list = []

for row in results:
    tweets_list.append(row[0])
    row_ht = [x.lower() for x in row[1].split(',') if x != '']
    row_mt = [x.lower() for x in row[2].split(',') if x != '']
    hashtags_list.extend(row_ht)
    mentions_list.extend(row_mt)

tweets_words_list = [tweet_toks(x) for x in tweets_list]
tweets_words = list(itertools.chain(*tweets_words_list))

tweets_freqdict = FreqDist(tweets_words)
ht_freqdict = FreqDist(hashtags_list)
mt_freqdict = FreqDist(mentions_list)

'''plot frequency plots'''
sns.set(font_scale=0.7)
sns.set_style("whitegrid")
fig, axes = plt.subplots(2, 2)

tweets_df = pd.DataFrame(tweets_freqdict.most_common(MOST_COMMON), columns=['words', 'count'])
ht_df = pd.DataFrame(ht_freqdict.most_common(MOST_COMMON), columns=['words', 'count'])
mt_df = pd.DataFrame(mt_freqdict.most_common(MOST_COMMON), columns=['words', 'count'])

tweets_df.sort_values(by='count').plot.barh(x='words', y='count', ax=axes[0, 0], color="purple")
ht_df.sort_values(by='count').plot.barh(x='words', y='count', ax=axes[0, 1], color="blue")
mt_df.sort_values(by='count').plot.barh(x='words', y='count', ax=axes[1, 0], color="magenta")

axes[0, 0].set_title('Tweets word frequency')
axes[0, 1].set_title('hashtags frequency')
axes[1, 0].set_title('mentions frequency')

plt.tight_layout()
plt.show()
# plt.savefig(f'{current_file_dir}/most_common_{MOST_COMMON}.png')
