'''Solve import issue'''
import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f'{current_file_dir}/../../'
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import traceback
from datetime import datetime
from tqdm import tqdm
from twitter_datasets.utils.twitter_scraper_utils import get_single_tweet_by_id
from utils.all_utils import program_sleep

ID_FILES_ROOT = './UIUC_dataset/'

class UIUC_SCRAPER:
    def __init__(self):
        self.id_files = []
        for folder in os.listdir(ID_FILES_ROOT):
            month_root = f'{ID_FILES_ROOT}{folder}/'
            for id_file in os.listdir(month_root):
                self.id_files.append(f'{month_root}{id_file}')
        self.id_files.sort()
        
        self.next_batch_ptr = 0
        self.log_file = f'../logs/uiuc_scraper_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

    def get_todb_by_file(self, id_file):
        print(f'Getting Tweets in {id_file}...')
        id_list = []
        all_tweets_todb = []
        images_todb = []
        videos_todb = []
        gifs_todb = []
        externals_todb = []
        covid19_tweets_todb = []

        with open(id_file, 'r') as infile:
            for line in infile:
                tweet_id = line.strip()
                id_list.append(tweet_id)

        for tweet_id in tqdm(id_list):
                successful = False
                while not successful:
                    try:
                        obj = get_single_tweet_by_id(tweet_id)
                        if obj:
                            all_tweets_todb.append([obj['tweet_id'], obj['full_text'], obj['created_at'], 
                                                    obj['language'], obj['hashtags_str'], obj['favorite_count'], obj['retweet_count']])
                            for media in obj['all_media_urls']:
                                if media['media_type'] == 'photo':
                                    images_todb.append([tweet_id, media['media_url']])
                                elif media['media_type'] == 'video':
                                    videos_todb.append([tweet_id, media['media_url']])
                                elif media['media_type'] == 'animated_gif':
                                    gifs_todb.append([tweet_id, media['media_url']])
                                elif media['media_type'] == 'other':
                                    externals_todb.append([tweet_id, media['media_url']])
                            covid19_tweets_todb.append([tweet_id])
                        successful = True
                    except Exception as e:
                        error_code = str(e).split('}]:')[0]
                        error_code = error_code.split('\'code\': ')[1]
                        if error_code == '88':
                            print('Rate limit exceeded!')
                            program_sleep(300)
                        else:
                            with open(self.log_file, 'a') as outfile:
                                outfile.writelines(f'{e}\n')
                            successful = True
        
        return {'all_tweets':all_tweets_todb, 'images':images_todb, 'videos':videos_todb, 
                'gifs':gifs_todb, 'externals':externals_todb, 'covid19_tweets':covid19_tweets_todb}

    def has_next_batch(self):
        return self.next_batch_ptr < len(self.id_files)

    def next_batch(self):
        id_file = self.id_files[self.next_batch_ptr]
        obj = self.get_todb_by_file(id_file)
        self.next_batch_ptr += 1
        return obj
