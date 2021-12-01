from datetime import datetime, timedelta

import datefinder
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Initialize constants.
ARTICLES_TO_EXTRACT_PER_DAY = 4

current_time = datetime.today()
time_two_weeks_back = current_time - timedelta(days=13)
print(f"\nParsing data from {time_two_weeks_back} to {current_time}")

# Generate a list of links that fetches news release of past two weeks.
filtered_link_list = []
for single_date in pd.date_range(time_two_weeks_back, current_time):
    filtered_link_list.append(f"https://www.prnewswire.com/news-releases/news-releases-list/"
                              f"?page=1&pagesize={ARTICLES_TO_EXTRACT_PER_DAY}&month={single_date.month:02}"
                              f"&day={single_date.day:02}&year={single_date.year:04}&hour={single_date.hour:02}")
print(filtered_link_list)

# Generate a list of required blog links.
blogs_link_list = []
for i in tqdm(filtered_link_list):
    response = requests.get(i)
    home_page = BeautifulSoup(response.text, 'html.parser')
    news_release_list = list(home_page.find_all("a", attrs={'class': 'newsreleaseconsolidatelink display-outline'}))
    # Generate links to each articles.
    blogs_link_list.extend([f"https://www.prnewswire.com{i.attrs.get('href')}" for i in news_release_list if i.attrs.get("href","")])
print(blogs_link_list)

# Loop through blog links, parse article body, date and add to dataframe.
data = pd.DataFrame(columns=["url", "article_date", "article_content"])
for i in blogs_link_list:
    blog = requests.get(i)
    blog_soup = BeautifulSoup(blog.text, 'html.parser')
    blog_body = blog_soup.find("section", attrs={'class': 'release-body container'})
    if not blog_body:
        blog_body = blog_soup.find("section", attrs={'class': 'release-body container '})
    blog_body = blog_body.text if blog_body else ""

    # Fetch article date.
    blog_date = blog_soup.find("meta", attrs={'name': 'date'}).attrs.get("content")
    matches = list(datefinder.find_dates(blog_date))
    blog_date = str(matches[0]) if matches else ""

    # Append to dataframe.
    data = data.append({
        "url": i,
        "article_date": blog_date,
        "article_content": blog_body},
        ignore_index=True)

print(data)
