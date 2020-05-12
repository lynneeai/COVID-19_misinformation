import json
import tweepy
from twitter_api_config import API_CONFIG

api_config = API_CONFIG()

auth = tweepy.OAuthHandler(api_config.consumer_key, api_config.consumer_secret)
auth.set_access_token(api_config.access_token_key, api_config.access_token_secret)

api = tweepy.API(auth)

id = '1260098159541452800'

def get_single_tweet_by_id(id, api):
    status = api.get_status(id, tweet_mode='extended')
    status_json = json.dumps(status._json)
    status_dict = json.loads(status_json)
    print(json.dumps(status_dict, indent=4, sort_keys=False))

    # tweet
    full_text = status.full_text
    text_range = status.display_text_range
    real_tweet = full_text[text_range[0]:text_range[1]]

    # hashtags
    all_hashtags = status_dict['entities']['hashtags']
    hashtags_str = ''
    for hashtag in all_hashtags:
        tag_text = hashtag['text']
        hashtags_str += f'#{tag_text}'

    # all media
    try:
        # images, videos and GIFs
        all_media = status_dict['extended_entities']['media']
        all_media_urls = []
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
        all_media_urls = []
        first_url_idx = float('inf')
        for media in all_media:
            all_media_urls.append(media['expanded_url'])
            first_url_idx = min(first_url_idx, media['indices'][0])
        
        # update tweet
        real_tweet = full_text[text_range[0]:first_url_idx]

    print(real_tweet)
    print(hashtags_str)
    print(all_media_urls)
    return {'real_tweet':real_tweet, 'hashtags_str':hashtags_str, 'all_media_urls':all_media_urls}


get_single_tweet_by_id(id, api)
