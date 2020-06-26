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
import traceback
import botometer
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from nltk import FreqDist
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict
from urllib.parse import urlparse
from twitter_datasets.utils.tweets_utils import tweet_toks
from utils.all_utils import print_dict
from utils.sqlite_utils import get_columns_values
from twitter_datasets.utils.api_keys import TWITTER_API_KEYS, RAPID_API_KEYS

'''
Read data and preprocess
'''

DB_FILE = f'{current_file_dir}/election_stream.db'
CONN = sqlite3.connect(DB_FILE)
CUR = CONN.cursor()

regular_tweets_results = get_columns_values('regular_tweets', ['tweet_id', 'author_id', 'created_at', 'text', 
										               'expanded_urls', 'hashtags_str', 'mentions_str', 
										               'like_count', 'quote_count', 'reply_count', 'retweet_count'], CUR)
retweets_results = get_columns_values('retweets', ['tweet_id', 'author_id', 'created_at', 'parent_tweet_id', 'parent_tweet_author_id', 
							               'like_count', 'quote_count', 'reply_count', 'retweet_count', 'text'], CUR)    
CONN.commit()
CONN.close()        

regular_tweets_dict = {}
retweets_dict = {}

for row in regular_tweets_results:
    tweet_id, author_id, created_at, text = row[0], row[1], row[2], row[3]
    expanded_urls = [x for x in row[4].split(',') if x != '']
    hashtags_str = [x.lower() for x in row[5].split(',') if x != '']
    mentions_str = [x.lower() for x in row[6].split(',') if x != '']
    like_count, quote_count, reply_count, retweet_count = int(row[7]), int(row[8]), int(row[9]), int(row[10])
    regular_tweets_dict[tweet_id] = {'author_id':author_id, 'created_at':created_at, 'text':text, 
									 'expanded_urls':expanded_urls, 'hashtags_str':hashtags_str, 'mentions_str':mentions_str, 
									 'like_count':like_count, 'quote_count':quote_count, 'reply_count':reply_count, 'retweet_count':retweet_count}
for row in retweets_results:
    tweet_id, author_id, created_at, parent_tweet_id, parent_tweet_author_id, text = row[0], row[1], row[2], row[3], row[4], row[9]
    like_count, quote_count, reply_count, retweet_count = int(row[5]), int(row[6]), int(row[7]), int(row[8])
    retweets_dict[tweet_id] = {'author_id':author_id, 'created_at':created_at, 
                               'parent_tweet_id':parent_tweet_id, 'parent_tweet_author_id':parent_tweet_author_id, 
							   'like_count':like_count, 'quote_count':quote_count, 'reply_count':reply_count, 'retweet_count':retweet_count, 
                               'text':text}

tweets_retweets_dict = defaultdict(list)
direct_tweets, undirect_tweets = 0, 0
for retweet_id, retweet_obj in retweets_dict.items():
    parent_tweet_id = retweet_obj['parent_tweet_id']
    if parent_tweet_id in regular_tweets_dict:
        direct_tweets += 1
    else:
        undirect_tweets += 1

    try:
        while parent_tweet_id not in regular_tweets_dict:
            # print(parent_tweet_id)
            parent_tweet_id = retweets_dict[parent_tweet_id]['parent_tweet_id']
            
        tweets_retweets_dict[parent_tweet_id].append(retweet_id)
    except:
        pass

tweets_retweets_count = []
for t, rts in tweets_retweets_dict.items():
    rt_count = regular_tweets_dict[t]['retweet_count']
    rts_len = len(rts)
    # print(f'tweet_id: {t}; retweet_count: {rt_count}; retweets_len: {rts_len}')
    tweets_retweets_count.append((t, rts_len))
tweets_retweets_count.sort(key=lambda x: x[1], reverse=True)

print(f'len(tweets_retweets_dict): {len(tweets_retweets_dict)}')
print(f'len(regular_tweets_dict): {len(regular_tweets_dict)}')
print(f'len(retweets_dict): {len(retweets_dict)}')
print(f'direct_tweets: {direct_tweets}')
print(f'undirect_tweets: {undirect_tweets}')
print(tweets_retweets_count[:20])


'''
Most retweeted tweets word frequency and urls
'''
# word freq
sns.set_style("whitegrid")
fig, axes = plt.subplots(2, 2)

most_retweeted_tweets = tweets_retweets_count[:10]
tweets_words_list = [tweet_toks(regular_tweets_dict[x[0]]['text']) for x in most_retweeted_tweets]
tweets_words = list(itertools.chain(*tweets_words_list))
tweets_freqdict = FreqDist(tweets_words)
tweets_df_10 = pd.DataFrame(tweets_freqdict.most_common(20), columns=['words', 'count'])
tweets_df_10.sort_values(by='count').plot.barh(x='words', y='count', ax=axes[0, 0], color="purple")

most_retweeted_tweets = tweets_retweets_count[:20]
tweets_words_list = [tweet_toks(regular_tweets_dict[x[0]]['text']) for x in most_retweeted_tweets]
tweets_words = list(itertools.chain(*tweets_words_list))
tweets_freqdict = FreqDist(tweets_words)
tweets_df_20 = pd.DataFrame(tweets_freqdict.most_common(20), columns=['words', 'count'])
tweets_df_20.sort_values(by='count').plot.barh(x='words', y='count', ax=axes[0, 1], color="purple")

most_retweeted_tweets = tweets_retweets_count[:50]
tweets_words_list = [tweet_toks(regular_tweets_dict[x[0]]['text']) for x in most_retweeted_tweets]
tweets_words = list(itertools.chain(*tweets_words_list))
tweets_freqdict = FreqDist(tweets_words)
tweets_df_50 = pd.DataFrame(tweets_freqdict.most_common(20), columns=['words', 'count'])
tweets_df_50.sort_values(by='count').plot.barh(x='words', y='count', ax=axes[1, 0], color="purple")

most_retweeted_tweets = tweets_retweets_count[:100]
tweets_words_list = [tweet_toks(regular_tweets_dict[x[0]]['text']) for x in most_retweeted_tweets]
tweets_words = list(itertools.chain(*tweets_words_list))
tweets_freqdict = FreqDist(tweets_words)
tweets_df_100 = pd.DataFrame(tweets_freqdict.most_common(20), columns=['words', 'count'])
tweets_df_100.sort_values(by='count').plot.barh(x='words', y='count', ax=axes[1, 1], color="purple")

axes[0, 0].set_title('Most tweeted 10 tweets word frequency')
axes[0, 1].set_title('Most tweeted 20 tweets word frequency')
axes[1, 0].set_title('Most tweeted 50 tweets word frequency')
axes[1, 1].set_title('Most tweeted 100 tweets word frequency')

plt.tight_layout()
plt.show()
plt.close()

# urls
url_list = []
for t in tweets_retweets_count[:100]:
    expanded_urls = regular_tweets_dict[t[0]]['expanded_urls']
    for url in expanded_urls:
        parsed_url = urlparse(url)
        result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)
        url_list.append(result)

sns.set_style("whitegrid")

url_freqdict = FreqDist(url_list)
url_df = pd.DataFrame(url_freqdict.most_common(20), columns=['url', 'count'])
url_df.sort_values(by='count').plot.barh(x='url', y='count', color="purple")

plt.title('Most common 20 urls')
plt.tight_layout()
# plt.show()
plt.close()


'''
bot detection
'''
twitter_api_keys = TWITTER_API_KEYS()
consumer_key = twitter_api_keys.consumer_key
consumer_secret = twitter_api_keys.consumer_secret
access_token = twitter_api_keys.access_token_key
access_token_secret = twitter_api_keys.access_token_secret
twitter_app_auth = {'consumer_key': consumer_key,
                    'consumer_secret': consumer_secret,
                    'access_token': access_token,
                    'access_token_secret': access_token_secret}

rapidapi_key = RAPID_API_KEYS().application_key

bom = botometer.Botometer(wait_on_ratelimit=True, rapidapi_key=rapidapi_key, **twitter_app_auth)

tweets_bot_percentages = []
for t, retweet_count in tqdm(tweets_retweets_count[:100]):
    rts = tweets_retweets_dict[t]
    accounts = [retweets_dict[x]['author_id'] for x in rts]
    bot_count = 0
    for screen_name, result in bom.check_accounts_in(accounts):
        try:
            if result['cap']['english'] > 0.5:
                bot_count += 1
        except:
            print(result)
    bot_percentage = bot_count / retweet_count
    tweets_bot_percentages.append((t, bot_percentage))
print(tweets_bot_percentages)

