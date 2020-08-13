import csv
import time
import sys
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

output_file = "../articles/Medicine-Today.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all links"""
article_urls = set()
url1 = "https://medicine-today.net/?s=coronavirus"
url2 = "https://medicine-today.net/?s=covid-19"
url3 = "https://medicine-today.net/?s=covid"

driver = webdriver.Chrome("/Users/lynnee/Tools/chromedriver")
SCROLL_PAUSE_TIME = 1

for url in [url1, url2, url3]:
    driver.get(url)
    time.sleep(SCROLL_PAUSE_TIME)
    # keep loading more until end
    while driver.find_element_by_class_name("mvp-inf-more-but").get_attribute("style") == "display: inline-block;":
        driver.find_element_by_class_name("mvp-inf-more-but").click()
        time.sleep(SCROLL_PAUSE_TIME)
    time.sleep(SCROLL_PAUSE_TIME)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    main_container = soup.find("ul", class_="mvp-main-blog-story left relative infinite-content")
    articles = main_container.find_all("div", class_="mvp-main-blog-out relative")
    for entry in articles:
        article_urls.add(entry.a["href"])

driver.quit()

"""get content for each article"""
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    main_content = soup.find("div", id="mvp-post-content-mid")

    # title
    header = main_content.find("header", id="mvp-post-head")
    title = header.find("h1", class_="mvp-post-title entry-title").get_text()

    # content
    article = main_content.find("section", id="mvp-content-main")
    text = article.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    metadata = header.find("span", class_="post-date updated")
    datetime = metadata.time["datetime"]

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})
