# coronavirus_misinfo

This repository scrapes and stores a SQLite database of COVID-19 misinformation articles.

All websites and articles come from the following source:
https://www.newsguardtech.com/coronavirus-misinformation-tracking-center/


The newsguard_tracked.db database contains the following table:

*all_articles*
```sql
CREATE TABLE all_articles (
    article_id INTEGER PRIMARY KEY, 
    title TEXT NOT NULL, 
    source TEXT NOT NULL, 
    content TEXT NOT NULL, 
    publishedAt TEXT, 
    url TEXT NOT NULL, 
    label TEXT
);
```