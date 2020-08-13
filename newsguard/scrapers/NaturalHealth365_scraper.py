import csv
import time
import sys
import requests
from bs4 import BeautifulSoup

output_file = "../articles/NaturalHealth365.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()


"""get all links"""
article_urls = set()
url1 = "https://www.naturalhealth365.com/?s=coronavirus"
url2 = "https://www.naturalhealth365.com/?s=covid-19"
url3 = "https://www.naturalhealth365.com/?s=covid"

for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, "html.parser")
        articles = soup.find_all("div", class_="article-container left")

        for entry in articles:
            item = entry.find_all("div", class_="title-meta-box")[0]
            article_urls.add(item.a["href"])

        # find next page url
        page_nav = soup.find_all("nav", class_="navigation")[0]
        next_button_container = page_nav.find_all("div", class_="nav-previous")[0]
        next_button = next_button_container.find_all("a")
        if next_button:
            url = next_button[0]["href"]
        else:
            break

"""get content for each article"""
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    # title
    title = soup.find("h1", class_="entry-title").get_text()

    # content
    article = soup.find("div", class_="pf-content")
    text = article.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    datetime = soup.find("span", class_="entry-date").get_text()

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})
