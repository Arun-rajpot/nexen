import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
from nltk import pos_tag, word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import json


# Load the sentiment words from CSV
csv_file_path = r"D:\industry_wise_news\Industry_News_Project\Utils\SentimentalWords.csv"
df_csv = pd.read_csv(csv_file_path)
sentiment_mapping = {'Negative': -1, 'Neutral': 0, 'Positive': 1}
word_sentiments_csv = dict(zip(df_csv['text'], df_csv['sentiment'].map(sentiment_mapping)))
sia = SentimentIntensityAnalyzer()


# Function to get sentence sentiment
def get_sentence_sentiment(sentence):
    words = word_tokenize(sentence.lower())
    csv_sentiment = sum(word_sentiments_csv.get(word, 0) for word in words)
    # print("csv_sentiment : ", csv_sentiment)
    nlp_sentiment = sia.polarity_scores(sentence)['compound']
    # print("nlp_sentiment : ", nlp_sentiment)
    combined_sentiment = csv_sentiment + nlp_sentiment

    if combined_sentiment > 0:
        return 'Positive'
    elif combined_sentiment < 0:
        return 'Negative'
    else:
        return 'Neutral'