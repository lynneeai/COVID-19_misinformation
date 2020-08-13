import csv
import time
import sys
import requests
from bs4 import BeautifulSoup

output_file = "../articles/JimBakkerShow.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all links"""
article_urls = set()
url1 = "https://jimbakkershow.com/?s=coronavirus"
url2 = "https://jimbakkershow.com/?s=covid-19"
url3 = "https://jimbakkershow.com/?s=covid"

for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, "html.parser")

        main_content = soup.find("div", class_="site-content")
        articles = main_content.find_all("article")

        for entry in articles:
            item = entry.find("h1", class_="entry-title")
            article_urls.add(item.a["href"])

        # find next page url
        page_nav = main_content.find("nav", class_="navigation-paging grid-100 alpha omega")
        next_button = page_nav.find_all("div", class_="nav-previous alignleft button")
        if next_button:
            url = next_button[0].a["href"]
        else:
            break

"""get content for each article"""
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    main_content = soup.find("div", class_="site-content").article

    # title
    header = main_content.find("header", class_="entry-header")
    title = header.find("h1", class_="entry-title").get_text()

    # content
    article = main_content.find("div", class_="entry-content")
    text = article.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    metadata = main_content.find("footer", class_="entry-meta")
    datetime = metadata.time["datetime"]

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})
