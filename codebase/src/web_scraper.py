import warnings
from datetime import datetime, timedelta

import datefinder
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

warnings.filterwarnings("ignore")

# Initialize constants.
ARTICLES_TO_EXTRACT_PER_DAY = 4


def generate_links_for_date_wise_news_releases() -> list:
    """
    Method to generate a list of links that fetches news release of past two weeks.
    :return: list of links to get date wise news releases.
    """

    # Get start and end date to fetch articles.
    current_time = datetime.now()
    time_two_weeks_back = current_time - timedelta(days=13)
    print(f"\nParsing news from " + time_two_weeks_back.strftime("%m/%d/%Y %H:00") + " to " + current_time.strftime("%m/%d/%Y %H:00") + "\n")

    # Generate a list of links that shows news release of past two weeks.
    filtered_link_list = []
    for single_date in pd.date_range(time_two_weeks_back, current_time):
        filtered_link_list.append(f"https://www.prnewswire.com/news-releases/news-releases-list/"
                                  f"?page=1&pagesize={ARTICLES_TO_EXTRACT_PER_DAY}&month={single_date.month:02}"
                                  f"&day={single_date.day:02}&year={single_date.year:04}&hour={single_date.hour:02}")

    # Display links.
    for itr in filtered_link_list:
        print(itr)

    return filtered_link_list


def generate_links_to_articles(filtered_news_links_list) -> list:
    """
    Method to generate a list of links to articles.

    :param filtered_news_links_list: list of links to news releases.
    :return articles_link_list: list of article links.
    """

    print("\n\nFetching links to articles from past two weeks..\n")

    # Looping through each date wise filtered news release links and fetching links to that days articles.
    articles_link_list = []
    for i in tqdm(filtered_news_links_list):
        response = requests.get(i)
        home_page = BeautifulSoup(response.text, 'html.parser')
        # Links to articles will be in the "a" tag with class "newsreleaseconsolidatelink display-outline".
        news_release_list = list(home_page.find_all("a", attrs={'class': 'newsreleaseconsolidatelink display-outline'}))
        # Adding all article links to one list.
        articles_link_list.extend(
            [f"https://www.prnewswire.com{i.attrs.get('href')}" for i in news_release_list if i.attrs.get("href", "")])
    print("\n\nFetching complete.\n\n")

    # Display all article links.
    for itr in articles_link_list:
        print(itr)

    print(f"\n\nNumber of articles: {len(articles_link_list)}")

    return articles_link_list


def parse_data_from_web(articles_link_list) -> pd.DataFrame:
    """
    Method to loop through article links, parse article body, date and add to dataframe.
    :param articles_link_list: list of links to articles.
    :return: Parsed data in dataframe.
    """

    print("\n\nExtracting information from scrapped content..\n")

    # Define dataframe.
    data = pd.DataFrame(columns=["url", "article_date", "article_content"])

    # Looping through article links and parsing, retrieving, storing information.
    for i in tqdm(articles_link_list):
        blog = requests.get(i)
        blog_soup = BeautifulSoup(blog.text, 'html.parser')
        # Article body is present in "section tag" with class "release-body container"
        blog_body = blog_soup.find("section", attrs={'class': 'release-body container'})
        if not blog_body:
            blog_body = blog_soup.find("section", attrs={'class': 'release-body container '})
        blog_body = blog_body.text if blog_body else ""

        # Fetch article date which is present in "meta" tag.
        blog_date = blog_soup.find("meta", attrs={'name': 'date'}).attrs.get("content", "")
        matches = list(datefinder.find_dates(blog_date))
        blog_date = str(matches[0]) if matches else ""

        # Append retrieved information to dataframe.
        data = data.append({
            "url": i,
            "article_date": blog_date,
            "article_content": blog_body},
            ignore_index=True)

    print("\nExtraction complete. All information added to dataframe.")

    return data


def store_data_as_excel(df):
    """
    Method to store data in dataframe as excel.
    :param df: parsed data in dataframe.
    :return None:
    """

    # Saving dataframe as excel with pandas to_excel function.
    df.to_excel(f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_scrapped_data.xlsx", index=False)


# ######### MAIN ###############
date_wise_news_releases_links = generate_links_for_date_wise_news_releases()
articles_links = generate_links_to_articles(date_wise_news_releases_links)
data = parse_data_from_web(articles_links)
store_data_as_excel(data)

print(data)
