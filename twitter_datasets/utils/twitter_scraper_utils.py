'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import json
import tweepy
import requests
import time
import traceback
from TwitterAPI import TwitterAPI
from utils.all_utils import print_dict
from api_keys import TWITTER_API_KEYS

twitter_api_keys = TWITTER_API_KEYS()
consumer_key = twitter_api_keys.consumer_key
consumer_secret = twitter_api_keys.consumer_secret
access_token_key = twitter_api_keys.access_token_key
access_token_secret = twitter_api_keys.access_token_secret

# api using Tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)
TWEEPY_API = tweepy.API(auth)

# api using TwitterAPI
TAPI_API = TwitterAPI(consumer_key, consumer_secret, access_token_key, access_token_secret) 

def get_tweet_details(tweet_dict, extended_mode=False, get_media_urls=False):
    try:
        # print_dict(tweet_dict)
        # tweet id
        tweet_id = tweet_dict['id_str']

        # tweet
        if extended_mode:
            full_text = tweet_dict['full_text']
            text_range = tweet_dict['display_text_range']
            
        else:
            full_text = tweet_dict['text']
            text_range = [0, len(full_text)]
        
        real_tweet = full_text[text_range[0]:text_range[1]]

        # time
        created_at = tweet_dict['created_at']

        # hashtags
        all_hashtags = tweet_dict['entities']['hashtags']
        hashtags_str = ','.join([f"#{tag['text']}" for tag in all_hashtags])

        # user mentions
        all_user_mentions = tweet_dict['entities']['user_mentions']
        mentions_str = ','.join([f"@{at['screen_name']}" for at in all_user_mentions])

        # language
        language = tweet_dict['lang']

        # favorite count
        favorite_count = tweet_dict['favorite_count']

        # retweet count
        retweet_count = tweet_dict['retweet_count']

        # all media
        all_media_urls = []
        if get_media_urls:
            try:
                # images, videos and GIFs
                all_media = tweet_dict['extended_entities']['media']
                for media in all_media:
                    media_type = media['type']
                    if media_type == 'photo':
                        media_url = media['media_url']
                    elif media_type == 'video' or 'animated_gif':
                        video_info = media['video_info']
                        all_urls = [x for x in video_info['variants'] if 'bitrate' in x]
                        all_urls.sort(key=lambda x: x['bitrate'])
                        media_url = all_urls[-1]['url']

                    all_media_urls.append({'media_type':media_type, 'media_url':media_url})

            except KeyError:
                # articles
                all_media = tweet_dict['entities']['urls']
                for media in all_media:
                    all_media_urls.append({'media_type':'other', 'media_url':media['expanded_url']})

        return {'tweet_id':tweet_id, 'full_text':real_tweet, 'created_at':created_at, 'language':language,
                'hashtags_str':hashtags_str, 'mentions_str':mentions_str, 'favorite_count':favorite_count,
                'retweet_count':retweet_count, 'all_media_urls':all_media_urls}
    
    except Exception:
        print(traceback.format_exc())
        return None

def get_single_tweet_by_id(id, extended_mode=True, get_media_urls=True):
    try:
        if extended_mode:
            tweet_obj = TWEEPY_API.get_status(id, tweet_mode='extended')
        else:
            tweet_obj = TWEEPY_API.get_status(id)

    except Exception as e:
        raise Exception(f'{e}: {id}')

    return get_tweet_details(tweet_obj._json, extended_mode=extended_mode, get_media_urls=get_media_urls)

def premium_search(product, label, query, from_date, to_date, bearer_token, max_results=100, next_token=None):
    endpoint_url = f'https://api.twitter.com/1.1/tweets/search/{product}/{label}.json'
    try:
        if next_token:
            params = {'query': query,
                      'fromDate': from_date,
                      'toDate': to_date,
                      'maxResults': max_results,
                      'next': next_token}
        else:
            params = {'query': query,
                      'fromDate': from_date,
                      'toDate': to_date,
                      'maxResults': max_results}

        response = requests.get(endpoint_url, auth=bearer_token, params=params)
        # print_dict(response.json())

        tweets_details = []
        for tweet_dict in response.json()['results']:
            details = get_tweet_details(tweet_dict)
            if details:
                tweets_details.append(details)

        response_json = response.json()
        if 'next' not in response_json:
            next_token = 'Not existed!'
        else:
            next_token = response.json()['next']

    except Exception as e:
        raise Exception(f'{response.status_code}: {e}')

    # print(tweets_details)
    return tweets_details, next_token

def get_retweet_detail(tweet_dict):
    try:
        # tweet id
        tweet_id = tweet_dict['id_str']

        # author id
        author_id = tweet_dict['user']['id_str']

        # time
        created_at = tweet_dict['created_at']

        # tweet
        text = tweet_dict['text']

        # retweet
        is_retweet = False
        parent_tweet_id = ''
        parent_tweet_author_id = ''
        if 'retweeted_status' in tweet_dict:
            is_retweet = True
            parent_tweet_id = tweet_dict['retweeted_status']['id_str']
            parent_tweet_author_id = tweet_dict['retweeted_status']['user']['id_str']

        # stats
        like_count = tweet_dict['favorite_count']
        quote_count = tweet_dict['quote_count']
        reply_count = tweet_dict['reply_count']
        retweet_count = tweet_dict['reply_count']
    
    except Exception:
        print(traceback.format_exc())
        return None

    return {'is_retweet':is_retweet,'tweet_id':tweet_id, 'author_id':author_id, 'created_at':created_at, 
            'parent_tweet_id':parent_tweet_id, 'parent_tweet_author_id':parent_tweet_author_id, 
            'like_count':like_count, 'quote_count':quote_count, 'reply_count':reply_count, 'retweet_count':retweet_count, 'text':text}

def premium_search_retweet(product, label, query, from_date, to_date, bearer_token, max_results=100, next_token=None):
    endpoint_url = f'https://api.twitter.com/1.1/tweets/search/{product}/{label}.json'
    try:
        if next_token:
            params = {'query': query,
                      'fromDate': from_date,
                      'toDate': to_date,
                      'maxResults': max_results,
                      'next': next_token}
        else:
            params = {'query': query,
                      'fromDate': from_date,
                      'toDate': to_date,
                      'maxResults': max_results}

        response = requests.get(endpoint_url, auth=bearer_token, params=params)

        # print_dict(response.json())

        tweets_details = []
        for tweet_dict in response.json()['results']:
            details = get_retweet_detail(tweet_dict)
            if details:
                tweets_details.append(details)

        response_json = response.json()
        if 'next' not in response_json:
            next_token = 'Not existed!'
        else:
            next_token = response.json()['next']

    except Exception as e:
        raise Exception(f'{response.status_code}: {e}')

    # print(tweets_details)
    return tweets_details, next_token

def get_tweet_details_labs(tweet_dict, metric_fieldname='stats'):
    data = tweet_dict['data']
    # if is retweet
    # returns  tweet_id, author_id, created_at, parent_tweet_id, parent_tweet_author_id, like_count, quote_count, reply_count, retweet_count
    if 'referenced_tweets' in data:
        for referred in data['referenced_tweets']:
            if referred['type'] == 'retweeted':
                all_referred_details = tweet_dict['includes']['tweets']
                parent_tweet_author_id = [item['author_id'] for item in all_referred_details if item['id'] == referred['id']][0]
                r_obj = {'is_retweet': True,
                         'is_reply': False,
                         'tweet_id': data['id'],
                         'author_id': data['author_id'],
                         'created_at': data['created_at'],
                         'text': data['text'],
                         'parent_tweet_id': referred['id'],
                         'parent_tweet_author_id': parent_tweet_author_id,
                         'like_count': data[metric_fieldname]['like_count'],
                         'quote_count': data[metric_fieldname]['quote_count'],
                         'reply_count': data[metric_fieldname]['reply_count'],
                         'retweet_count': data[metric_fieldname]['retweet_count']}
                return r_obj
            elif referred['type'] == 'replied_to':
                r_obj = {'is_retweet': False,
                         'is_reply': True,
                         'tweet_id': data['id'],
                         'parent_tweet_id': referred['id']}
                return r_obj

    expanded_urls = ''
    hashtags_str = ''
    mentions_str = ''
    if 'entities' in data:
        # if not retweet
        # returns tweet_id, author_id, created_at, text, expanded_urls, hashtags_str, mentions_str, like_count, quote_count, reply_count, retweet_count
        # expanded_urls
        if 'urls' in data['entities']:
            expanded_urls = [item['expanded_url'] for item in data['entities']['urls'] if 'expanded_url' in item]
            unwound_urls = [item['unwound_url'] for item in data['entities']['urls'] if 'unwound_url' in item]
            expanded_urls.extend(unwound_urls)
            expanded_urls = ','.join(expanded_urls)
        # hashtags
        if 'hashtags' in data['entities']:
            all_hashtags = data['entities']['hashtags']
            hashtags_str = ','.join([f"#{tag['tag']}" for tag in all_hashtags])
        # user mentions
        if 'mentions' in data['entities']:
            all_user_mentions = data['entities']['mentions']
            mentions_str = ','.join([f"@{at['username']}" for at in all_user_mentions])

    r_obj = {'is_retweet': False,
             'is_reply': False,
             'tweet_id': data['id'],
             'author_id': data['author_id'],
             'created_at': data['created_at'],
             'text': data['text'],
             'expanded_urls': expanded_urls,
             'hashtags_str': hashtags_str,
             'mentions_str': mentions_str,
             'like_count': data[metric_fieldname]['like_count'],
             'quote_count': data[metric_fieldname]['quote_count'],
             'reply_count': data[metric_fieldname]['reply_count'],
             'retweet_count': data[metric_fieldname]['retweet_count']}

    return r_obj
    
def get_single_tweet_by_id_labs(id, bearer_token):
    endpoint_url = f'https://api.twitter.com/labs/2/tweets/{id}'
    params = {'tweet.fields':'created_at,entities,public_metrics,author_id,referenced_tweets',
              'expansions':'referenced_tweets.id'}
    response = requests.get(endpoint_url, auth=bearer_token, params=params)
    if response.status_code > 201:
        # print_dict(params)
        raise Exception(f'{response.status_code}: {response.text}')
    # print(f'{response.status_code}: {response.text}')
    # print_dict(response.json())

    r_json = response.json()
    if 'errors' in r_json:
        raise Exception(f'[Self Defined]Error in response!')

    return get_tweet_details_labs(response.json(), metric_fieldname='public_metrics')

def recent_search_labs(query, start_time, end_time, next_token, bearer_token):
    endpoint_url = f'https://api.twitter.com/labs/2/tweets/search'
    headers = {"Accept-Encoding": "gzip"}
    if next_token:
        params = {'query':query,
                  'tweet.fields':'created_at,entities,public_metrics,author_id,referenced_tweets',
                  'start_time':start_time,
                  'end_time':end_time,
                  'max_results':100,
                  'next_token':next_token}
    else:
        params = {'query':query,
                  'tweet.fields':'created_at,entities,public_metrics,author_id,referenced_tweets',
                  'start_time':start_time,
                  'end_time':end_time,
                  'max_results':100}

    response = requests.get(endpoint_url, auth=bearer_token, headers=headers, params=params)
    if response.status_code > 201:
        print_dict(params)
        raise Exception(f'{response.status_code}: {response.text}')

    r_json = response.json()
    tweet_dicts = r_json['data']
    if 'next_token' in r_json['meta']:
        next_token = r_json['meta']['next_token']
    else:
        next_token = 'Does not exist!'

    r_obj_list = []
    for tweet_dict in tweet_dicts:
        try:
            tweet_dict = {'data':tweet_dict}
            r_obj_list.append(get_tweet_details_labs(tweet_dict, metric_fieldname='public_metrics'))
        except Exception as e:
            print(e)
    
    return {'r_obj_list':r_obj_list, 'next_token':next_token}
