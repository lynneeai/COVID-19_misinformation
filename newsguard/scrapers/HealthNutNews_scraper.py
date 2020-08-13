import csv
import time
import sys
import requests
from bs4 import BeautifulSoup

output_file = "../articles/HealthNutNews.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all links"""
article_urls = set()
url1 = "https://www.healthnutnews.com/?s=coronavirus"
url2 = "https://www.healthnutnews.com/?s=covid-19"
url3 = "https://www.healthnutnews.com/?s=covid"

for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, "html.parser")

        main_content = soup.find("div", class_="et_pb_extra_column_main")
        articles = main_content.find_all("article")

        for entry in articles:
            item = entry.find("div", class_="header")
            article_urls.add(item.a["href"])

        # find next page url
        page_nav = soup.find("div", class_="archive-pagination")
        next_button = page_nav.find_all("li", class_="next")
        if next_button:
            url = next_button[0].a["href"]
        else:
            break

"""get content for each article"""
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    main_content = soup.find("div", class_="et_pb_extra_column_main").article

    # title
    header = main_content.find("div", class_="post-header")
    title = header.find("h1", class_="entry-title").get_text()

    # content
    article = main_content.find("div", class_="post-content entry-content")
    text = article.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    metadata = header.find("div", class_="post-meta vcard")
    datetime = metadata.find("span", class_="updated").get_text()

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})
