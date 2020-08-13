import csv
import time
import sys
import requests
from bs4 import BeautifulSoup

output_file = "../articles/Intellihub.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all links"""
article_urls = dict()
url1 = "https://www.intellihub.com/?s=coronavirus"
url2 = "https://www.intellihub.com/?s=covid-19"
url3 = "https://www.intellihub.com/?s=covid"

SLEEP_TIME = 60


def sleep_countdown(sleep_time):
    for i in range(sleep_time, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write(f"Sleeping for {str(i)} sec...")
        sys.stdout.flush()
        time.sleep(1)
    print()


for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, "html.parser")
        try:
            main_section = soup.find_all("div", class_="td-ss-main-content")[0]
            articles = main_section.find_all("div", class_="td-block-span6")
            for entry in articles:
                title_item = entry.find_all("h3", class_="entry-title td-module-title")[0]
                url = title_item.a["href"]
                title = title_item.a.get_text()
                datetime = entry.find("div", class_="td-post-date").time["datetime"]
                article_urls[url] = (title, datetime)

            # find next page url
            page_nav = main_section.find_all("div", class_="page-nav td-pb-padding-side")[0]
            all_pages = page_nav.find_all("a")
            for p in all_pages:
                next_button = p.find_all("i", class_="td-icon-menu-right")
                if next_button:
                    url = p["href"]
            if not next_button:
                break
        except:
            print(url)
            print("Access exceeded!")
            sleep_countdown(SLEEP_TIME)

"""get content for each article"""
for link, (title, datetime) in article_urls.items():
    successful = False
    while not successful:
        try:
            req = requests.get(link)
            page = req.content
            soup = BeautifulSoup(page, "html.parser")

            main_content = soup.find_all("div", class_="td-ss-main-content")[0]

            # # title
            # header = main_content.header
            # title = header.find_all('h1', class_='entry-title')[0].get_text()

            # content
            article = main_content.find_all("div", class_="td-post-content")[0]
            text = article.find_all(["p", "li", "h1", "h2", "h3"])
            content = "\n".join([i.get_text() for i in text])

            # # publishedAt
            # metadata = header.find_all('div', class_='td-module-meta-info')[0]
            # datetime = metadata.time['datetime']

            with open(output_file, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})

            successful = True

        except Exception as e:
            print(link)
            if req.status_code == 503:
                print("Access exceeded!")
                sleep_countdown(SLEEP_TIME)
            else:
                print(e)
