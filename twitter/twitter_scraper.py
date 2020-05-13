'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import json
import tweepy
import traceback
from twitter_api_key import API_KEY

api_key = API_KEY()
auth = tweepy.OAuthHandler(api_key.consumer_key, api_key.consumer_secret)
auth.set_access_token(api_key.access_token_key, api_key.access_token_secret)
API = tweepy.API(auth)

def get_single_tweet_by_id(id):
    try:
        status = API.get_status(id, tweet_mode='extended')
        status_json = json.dumps(status._json)
        status_dict = json.loads(status_json)
        # print(json.dumps(status_dict, indent=4, sort_keys=False))

        # tweet
        full_text = status.full_text
        text_range = status.display_text_range
        real_tweet = full_text[text_range[0]:text_range[1]]

        # time
        created_at = status.created_at

        # hashtags
        all_hashtags = status_dict['entities']['hashtags']
        hashtags_str = ''
        for hashtag in all_hashtags:
            tag_text = hashtag['text']
            hashtags_str += f'#{tag_text}'

        # language
        language = status.lang

        # favorite count
        favorite_count = status.favorite_count

        # retweet count
        retweet_count = status.retweet_count

        # all media
        all_media_urls = []
        try:
            # images, videos and GIFs
            all_media = status_dict['extended_entities']['media']
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
            all_media = status_dict['entities']['urls']
            first_url_idx = text_range[1]
            for media in all_media:
                all_media_urls.append({'media_type':'other', 'media_url':media['expanded_url']})
                first_url_idx = min(first_url_idx, media['indices'][0])
            
            # update tweet
            real_tweet = full_text[text_range[0]:first_url_idx]

        return {'full_text':real_tweet, 'created_at':created_at, 'language':language,
                'hashtags_str':hashtags_str, 'favorite_count':favorite_count,
                'retweet_count':retweet_count, 'all_media_urls':all_media_urls}
    
    except Exception as e:
        # print(traceback.format_exc())
        raise Exception(f'{e}: {id}')

# id = '1260434329219538947'
# obj = get_single_tweet_by_id(id)