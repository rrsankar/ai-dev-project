import re
import warnings
from collections import deque
from datetime import datetime, timedelta

import datefinder
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import tensorflow as tf
import yfinance as yf
from bs4 import BeautifulSoup
from tqdm import tqdm

warnings.filterwarnings("ignore")

# Initialize constants.
ARTICLES_TO_EXTRACT_PER_DAY = 4


class Parser:
    """
    Class with methods to generate links to news releases, links to articles, parse/scrape articles and extract required information.
    """

    def __init__(self):
        pass

    def generate_links_for_date_wise_news_releases(self) -> list:
        """
        Method to generate a list of links that fetches news release of past two weeks.
        :return: list of links to get date wise news releases.
        """

        # Get start and end date to fetch articles.
        current_time = datetime.now()
        time_two_weeks_back = current_time - timedelta(days=13)
        print(f"\nParsing news from " + time_two_weeks_back.strftime("%m/%d/%Y %H:00") + " to " + current_time.strftime(
            "%m/%d/%Y %H:00") + "\n")

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

    def generate_links_to_articles(self, filtered_news_links_list) -> list:
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
            news_release_list = list(
                home_page.find_all("a", attrs={'class': 'newsreleaseconsolidatelink display-outline'}))
            # Adding all article links to one list.
            articles_link_list.extend(
                [f"https://www.prnewswire.com{i.attrs.get('href')}" for i in news_release_list if
                 i.attrs.get("href", "")])
        print("\n\nFetching complete.\n\n")

        # Display all article links.
        for itr in articles_link_list:
            print(itr)

        print(f"\n\nNumber of articles: {len(articles_link_list)}")

        return articles_link_list

    def parse_data_from_web(self, articles_link_list) -> pd.DataFrame:
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


class Tracker:
    """
    Class to store extracted data and fetch stock tickers from it.
    """

    def __init__(self, data):
        self.data = data

    def store_data_as_excel(self) -> None:
        """
        Method to store data in dataframe as excel.
        :return None:
        """

        # Saving dataframe as excel with pandas to_excel function.
        self.data.to_excel(f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_scrapped_data.xlsx", index=False)

    def preprocess_data(self) -> None:
        """
        Method to do preprocessing of data before extracting tickers.
        :return:
        """

        # Dropping duplicates if present.
        self.data.drop_duplicates(subset="article_content", inplace=True, ignore_index=True)

    def fetch_tickers(self) -> set:
        """
        Method to fetch tickers from all article content.
        :return: Set of tickers.
        """

        tickers = set()
        for i in range(len(self.data)):
            temp = re.findall(r':\s[A-Z]{1,5}[)]', self.data.iloc[i]["article_content"])
            for tick in temp:
                tickers.add(tick[-(len(tick) - 2):-1])
        return tickers


class Retriever:
    """
    Class to retrieve stock information for tickers found in scrapped content.
    """

    def __init__(self, tickers):
        self.tickers = tickers

    def retrieve(self) -> dict:
        """
        Method to retrieve ticker prices using yahoo finance api.
        :return: Stock information as dict.
        """
        stocks = {}
        for tick in self.tickers:
            stocks[tick] = yf.Ticker(tick).history(period="YTD")
        return stocks


class Visualizer:
    """
    Class to display visualization of stock information.
    """

    def __init__(self, stocks):
        self.stocks = stocks

    def generate_candle_stick_visualization(self, ticker, increasing_line, decreasing_line):
        fig = go.Figure(data=[go.Candlestick(
            x=self.stocks[ticker].index,
            open=self.stocks[ticker]['Open'],
            high=self.stocks[ticker]['High'],
            low=self.stocks[ticker]['Low'],
            close=self.stocks[ticker]['Close'],
            increasing_line_color=increasing_line,
            decreasing_line_color=decreasing_line)
            ])
        fig.update_layout(autosize=False,
                          width=1000,
                          height=800,)
        fig.show()

    def plot_tickers(self, ticker):
        fig = plt.figure(figsize=(30, 21))
        ax1 = plt.subplot(2, 2, 1)
        plt.xticks(rotation=45)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        ax2 = plt.subplot(2, 2, 2)
        plt.xticks(rotation=45)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        ax2.yaxis.offsetText.set_fontsize(20)
        ax1.plot(self.stocks[ticker]["Close"])
        ax2.plot(self.stocks[ticker]["Volume"])


class StockRecommender:
    """
    Class to predict if a stock is worth purchasing.
    """

    def __init__(self, stocks):
        self.stocks = stocks

        # Loading stock recommendation model.
        self.model = tf.keras.models.load_model("LSTM_stock")

    def model_predict(self, X):
        if np.argmax(self.model.predict(X)[-1]) == 0:
            print("Sell")
        else:
            print("buy")

    def preprocess(self, ticker):
        series = self.stocks[ticker]["Close"]
        series = series.pct_change()
        series = series.dropna()
        seq_data = []
        prev_days = deque(maxlen=100)
        for i in series:
            prev_days.append(i)
            if len(prev_days) == 100:
                seq_data.append([np.array(prev_days)])
            X = []
            for seq in seq_data:
                X.append(seq)
            X = np.array(X)
        return self.model_predict(X.reshape(-1, X.shape[2], X.shape[1]))


def main():

    # Web scraping.
    parser_obj = Parser()

    date_wise_news_releases_links = parser_obj.generate_links_for_date_wise_news_releases()
    articles_links = parser_obj.generate_links_to_articles(date_wise_news_releases_links)
    data = parser_obj.parse_data_from_web(articles_links)
    print(data)

    # Tracking: storing data and generating tickers.
    tracker_obj = Tracker(data)

    tracker_obj.store_data_as_excel()
    tracker_obj.preprocess_data()
    tickers = tracker_obj.fetch_tickers()

    # Retrieving stock info.
    retriever_obj = Retriever(tickers)

    stocks = retriever_obj.retrieve()

    # Visualization
    visualizer_obj = Visualizer(stocks)
    i_cl = ["gold", "green", "cyan"]
    d_cl = ["gray", "red", "black"]

    widgets.interact(visualizer_obj.generate_candle_stick_visualization, ticker=stocks.keys(), increasing_line=i_cl, decreasing_line=d_cl)
    widgets.interact(visualizer_obj.plot_tickers, ticker=stocks.keys())

    # Stock recommendation
    stock_recommender_obj = StockRecommender(stocks)

    widgets.interact(stock_recommender_obj.preprocess, ticker=stocks.keys())

main()
