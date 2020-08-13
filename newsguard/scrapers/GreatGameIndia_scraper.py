import csv
import requests
from bs4 import BeautifulSoup

output_file = "../articles/GreatGameIndia.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all article urls"""
article_urls = []
url = "https://greatgameindia.com/category/coronavirus-covid19/"
last_page = "-1"
while True:
    req = requests.get(url)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")
    articles = soup.find_all("div", class_="td_module_10 td_module_wrap td-animation-stack")
    for entry in articles:
        item = entry.find_all("a", class_="td-image-wrap")[0]
        article_urls.append(item["href"])

    # find next page url
    page_nav = soup.find_all("div", class_="page-nav td-pb-padding-side")[0]
    curr_page = page_nav.find("span", class_="current").get_text()
    if last_page == "-1":
        last_page = page_nav.find("a", class_="last").get_text()
    if curr_page == last_page:
        break
    all_pages = page_nav.find_all("a")
    for p in all_pages:
        next_button = p.find_all("i", class_="td-icon-menu-right")
        if next_button:
            url = p["href"]

"""get content for each article"""
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    # title
    header = soup.find_all("header", class_="td-post-title")[0]
    title = header.h1.get_text()

    # content
    main_content = soup.find_all("div", class_="td-post-content")[0]
    text = main_content.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    datetime = header.time["datetime"]

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})
