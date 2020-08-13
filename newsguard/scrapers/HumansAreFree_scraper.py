import csv
import time
import sys
import requests
from bs4 import BeautifulSoup

output_file = "../articles/HumansAreFree.csv"
fieldnames = ["title", "content", "publishedAt", "url"]
with open(output_file, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

"""get all links"""
article_urls = set()
url1 = "https://humansarefree.com/?s=coronavirus"
url2 = "https://humansarefree.com/?s=covid-19"
url3 = "https://humansarefree.com/?s=covid"

for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, "html.parser")

        main_content = soup.find("div", id="content_masonry")
        articles = soup.find_all("div", class_="post_grid_content_wrapper")

        for entry in articles:
            item = entry.find("div", class_="image-post-thumb")
            article_urls.add(item.a["href"])

        # find next page url
        page_nav = soup.find("nav", class_="jellywp_pagination")
        next_button = page_nav.find_all("a", class_="next page-numbers")
        if next_button:
            url = next_button[0]["href"]
        else:
            break

"""get content for each article"""
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, "html.parser")

    main_content = soup.find("div", class_="single_section_content box blog_large_post_style")

    # title
    header = main_content.find("div", class_="single_post_entry_content single_bellow_left_align")
    title = header.find("h1", class_="single_post_title_main").get_text()

    # content
    article = main_content.find("div", class_="post_content")
    text = article.find_all(["p", "li", "h1", "h2", "h3"])
    content = "\n".join([i.get_text() for i in text])

    # publishedAt
    metadata = header.find("span", class_="single-post-meta-wrapper")
    datetime = metadata.find("span", class_="post-date updated")["datetime"]

    with open(output_file, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({"title": title, "content": content, "publishedAt": datetime, "url": link})
