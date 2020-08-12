"""Solve import issue"""
import os
import sys

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

import traceback
import time
from datetime import datetime
from tqdm import tqdm
from twitter_datasets.utils.twitter_scraper_utils import get_single_tweet_by_id
from utils.all_utils import write_to_log

ID_FILES_ROOT = "./USC_dataset/"


class USC_SCRAPER:
    def __init__(self):
        self.id_files = []
        for folder in os.listdir(ID_FILES_ROOT):
            month_root = f"{ID_FILES_ROOT}{folder}/"
            for id_file in os.listdir(month_root):
                self.id_files.append(f"{month_root}{id_file}")
        self.id_files.sort(reverse=True)
        self.next_file_ptr = 14
        self.current_id_file = ""

        self.cached_ids = []
        self.next_cached_id_ptr = 29929
        self.log_file = f'../logs/usc_scraper_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

        self.is_first_batch = True

    def next_batch(self):
        if self.next_cached_id_ptr >= len(self.cached_ids):
            self.cached_ids = []
            self.next_cached_id_ptr = self.next_cached_id_ptr if self.is_first_batch else 0
            self.current_id_file = self.id_files[self.next_file_ptr]
            with open(self.current_id_file, "r") as infile:
                for line in infile:
                    tweet_id = line.strip()
                    self.cached_ids.append(tweet_id)

            write_to_log(
                self.log_file, f'-------[{datetime.now().strftime("%H:%M:%S")}] Starting processing file with idx {self.next_file_ptr}: {self.current_id_file}-------',
            )
            self.next_file_ptr += 1
            self.is_first_batch = False

        print(f"Getting Tweets in {self.current_id_file}...")

        limit_exceeded = False
        covid19_tweets_todb = []
        images_todb = []
        videos_todb = []
        gifs_todb = []
        externals_todb = []

        trange = tqdm(range(self.next_cached_id_ptr, len(self.cached_ids)))
        for idx in trange:
            tweet_id = self.cached_ids[idx]
            try:
                obj = get_single_tweet_by_id(tweet_id)
                if obj:
                    covid19_tweets_todb.append(
                        [obj["tweet_id"], obj["full_text"], obj["created_at"], obj["language"], obj["hashtags_str"], obj["mentions_str"], obj["favorite_count"], obj["retweet_count"],]
                    )
                    for media in obj["all_media_urls"]:
                        if media["media_type"] == "photo":
                            images_todb.append([tweet_id, media["media_url"]])
                        elif media["media_type"] == "video":
                            videos_todb.append([tweet_id, media["media_url"]])
                        elif media["media_type"] == "animated_gif":
                            gifs_todb.append([tweet_id, media["media_url"]])
                        elif media["media_type"] == "other":
                            externals_todb.append([tweet_id, media["media_url"]])

            except Exception as e:
                try:
                    error_code = str(e).split("}]:")[0]
                    error_code = error_code.split("'code': ")[1]
                    if error_code == "88":
                        limit_exceeded = True
                        self.next_cached_id_ptr = idx
                        write_to_log(
                            self.log_file, f'**[{datetime.now().strftime("%H:%M:%S")}]** Finished {idx} tweets in file {self.next_file_ptr - 1}! Next tweet idx: {self.next_cached_id_ptr}',
                        )
                        trange.close()
                        break
                    else:
                        write_to_log(self.log_file, f"{e}")
                except Exception as e:
                    write_to_log(self.log_file, f"{e}")

        trange.close()
        time.sleep(1)
        if not limit_exceeded:
            self.next_cached_id_ptr = len(self.cached_ids)
            write_to_log(
                self.log_file, f'-------[{datetime.now().strftime("%H:%M:%S")}] Finished processing file with idx {self.next_file_ptr - 1}: {self.current_id_file}-------\n',
            )

        return {
            "limit_exceeded": limit_exceeded,
            "covid19_tweets": covid19_tweets_todb,
            "images": images_todb,
            "videos": videos_todb,
            "gifs": gifs_todb,
            "externals": externals_todb,
        }

    def has_next_batch(self):
        return (self.next_file_ptr < len(self.id_files)) or (self.next_cached_id_ptr < len(self.cached_ids))
