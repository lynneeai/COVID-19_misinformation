import csv
import time
import requests
import pickle
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from tqdm import tqdm

REFETCH_URLS = False
url_temp_file = "./WND_urls"

output_file = "../articles/WND.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all article urls"""
if REFETCH_URLS:
    article_urls = set()
    url1 = "https://www.wnd.com/?s=coronavirus"
    url2 = "https://www.wnd.com/?s=covid-19"
    url3 = "https://www.wnd.com/?s=covid"

    driver = webdriver.Chrome("/Users/lynnee/Tools/chromedriver")
    SCROLL_PAUSE_TIME = 0.5
    EXTRA_WAIT = 60

    for url in [url1]:
        driver.get(url)
        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        extra_waited_count = 0
        prev_dt = datetime.now()
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                if extra_waited_count <= EXTRA_WAIT:
                    extra_waited_count += 1
                else:
                    break
            else:
                extra_waited_count = 0

            last_height = new_height

            # stop if date is unsorted
            soup = BeautifulSoup(driver.page_source, "html.parser")
            main_content = soup.find("div", class_="archive-latest")
            last = main_content.find_all("article")[-1]
            dt_s = last.find("span", class_="entry-date").get_text()
            dt_s = dt_s.split("at")[0].strip()
            dt = datetime.strptime(dt_s, "%B %d, %Y")
            if dt > prev_dt:
                break
            else:
                prev_dt = dt

        time.sleep(SCROLL_PAUSE_TIME)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        main_content = soup.find("div", class_="archive-latest")
        articles = main_content.find_all("article")
        for entry in articles:
            item = entry.find("div", class_="entry-image")
            article_urls.add(item.a["href"])

    driver.quit()

    print(len(article_urls))
    with open(url_temp_file, "wb") as fp:
        pickle.dump(article_urls, fp)

"""get content for each article"""
with open(url_temp_file, "rb") as fp:
    article_urls = pickle.load(fp)

for link in tqdm(article_urls):
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    # title
    header = soup.find("header", class_="entry-header")
    title = header.find("h1", class_="entry-title").get_text()

    # content
    article = soup.find("div", class_="entry-content")
    text = article.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    metadata = header.find("div", class_="entry-meta")
    dt = metadata.find_all("span")[1].get_text().split("Published ")[1].strip()

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": dt, "url": link})
