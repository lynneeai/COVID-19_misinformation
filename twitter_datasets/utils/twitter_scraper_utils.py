'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import json
import tweepy
import traceback
from twitter_api_config import API_CONFIG
from TwitterAPI import TwitterAPI
from utils.all_utils import print_dict

api_config = API_CONFIG()
consumer_key = api_config.consumer_key
consumer_secret = api_config.consumer_secret
access_token_key = api_config.access_token_key
access_token_secret = api_config.access_token_secret

# api using Tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)
TWEEPY_API = tweepy.API(auth)

# api using TwitterAPI
TAPI_API = TwitterAPI(consumer_key, consumer_secret, access_token_key, access_token_secret) 
PRODUCT = api_config.product_30
LABEL = api_config.label

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
				'hashtags_str':hashtags_str, 'favorite_count':favorite_count,
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

def premium_search(product, label, query, from_date, to_date, max_results=100):
	try:
		response = TAPI_API.request(f'tweets/search/{product}/:{label}', 
									{'query': query,
									'fromDate': from_date,
									'toDate': to_date,
									'maxResults': max_results})
	
	except Exception as e:
		raise Exception(f'{response.status_code}: {e}')
	
	tweets_details = []
	for tweet_dict in response:
		details = get_tweet_details(tweet_dict)
		if details:
			tweets_details.append(details)

	return tweets_details


# premium_search(PRODUCT, LABEL, f'#covid19 lang:en', '202005140000', '202005150000')
# print(get_single_tweet_by_id('1261195933859053568', extended_mode=False, get_media_urls=False))