"""Solve import issue"""
import os
import sys

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

from datetime import datetime, timedelta
from twitter_datasets.utils.twitter_scraper_utils import premium_search
from utils.all_utils import write_to_log, program_sleep


class HASHTAGS_SEARCHER:
    def __init__(self, product, label, hashtags, from_date, to_date, tweets_per_day, lang="en"):
        self.product = product
        self.label = label
        self.from_date = from_date
        self.to_date = to_date
        self.tweets_per_day = tweets_per_day

        self.query = " ".join(hashtags) + f" lang:{lang}"
        self.next_datetime = from_date

        log_filename = "".join(hashtags) + f"_{product}"
        self.log_file = f'../logs/{log_filename}_{datetime.now().strftime("%Y%m%d_%H:%M:%S")}.txt'

    def next_batch(self):
        tweets_todb = []
        from_date_str = self.next_datetime.strftime("%Y%m%d%H%M")
        to_date_str = (self.next_datetime + timedelta(days=1)).strftime("%Y%m%d%H%M")

        print(f"Searching for date {from_date_str}...")
        write_to_log(self.log_file, f'-------[{datetime.now().strftime("%H:%M:%S")}] Start searching for date {from_date_str}-------')

        tweets_count = 0
        next_token = None
        while tweets_count < self.tweets_per_day and next_token != "Not existed!":
            try:
                tweets_list, next_token = premium_search(product=self.product, label=self.label, query=self.query, from_date=from_date_str, to_date=to_date_str, next_token=next_token)
                tweets_count += len(tweets_list)
                for obj in tweets_list:
                    tweets_todb.append([obj["tweet_id"], obj["full_text"], obj["created_at"], obj["language"], obj["hashtags_str"], obj["mentions_str"], obj["favorite_count"], obj["retweet_count"]])
            except Exception as e:
                error_code = str(e).split(":")[0]
                if error_code == "88" or error_code == "429":
                    print("Rate limit exceeded!")
                    write_to_log(self.log_file, f'**[{datetime.now().strftime("%H:%M:%S")}]** Rate limit exceeded! Next date to search: {from_date_str}')
                    program_sleep(61)
                else:
                    write_to_log(self.log_file, f"{e}")
                    break

        self.next_datetime += timedelta(days=1)
        write_to_log(self.log_file, f'-------[{datetime.now().strftime("%H:%M:%S")}] Finished searching for date {from_date_str}-------\n')
        return tweets_todb

    def has_next_batch(self):
        return self.next_datetime < self.to_date


# s = HASHTAGS_SEARCHER('30days', 'dev', ['#covid19'], datetime.today() - timedelta(days=30), datetime.today(), 200)
# s.search()
