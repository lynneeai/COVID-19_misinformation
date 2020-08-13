import csv
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

output_file = "../articles/TheMindUnleashed.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all article urls"""
article_urls = set()
url1 = "https://themindunleashed.com/?s=coronavirus"
url2 = "https://themindunleashed.com/?s=covid-19"
url3 = "https://themindunleashed.com/?s=covid"

driver = webdriver.Chrome("/Users/lynnee/Tools/chromedriver")
SCROLL_PAUSE_TIME = 0.5

for url in [url1, url2, url3]:
    driver.get(url)
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    articles = soup.find_all("div", class_="article-card")
    for entry in articles:
        title = entry.find_all("h3", class_="article-card-title")[0]
        article_urls.add(title.a["href"])

driver.quit()

"""get content for each article"""
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    main_content = soup.find_all("div", class_="main-content")[0].article

    # title
    header = main_content.header
    title = header.find_all("h1", class_="entry-title")[0].get_text()

    # content
    article = main_content.find_all("div", class_="article-copy")[0]
    text = article.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    metadata = header.find_all("div", class_="entry-meta-top")[0]
    datetime = metadata.time["datetime"]

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})
