import os
import json
import spacy
import nltk
import requests
import time
import pandas as pd
from spacy import displacy
from nltk.tag import pos_tag
from bs4 import BeautifulSoup as bs
from nltk.tokenize import word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer


def push_news(news_payload):
    newsUrl = "http://103.233.79.196:8083/background_scheduler/news/processNews"
    header = {
        "Content-Type": "application/json"
    }

    resp = requests.post(url=newsUrl, data=json.dumps(news_payload), headers = header)
    print(resp.content)


class NewsData():
    global comp_cins, csv_file_path

    LABOUR_NEWS_TAG = ["Labour Strikes", "Strikes", "Quits", "unrest",
                       "agitation", "lock out", "termination", "ESI", "unrest", "Fired", "Quit", "suicide", "protest",
                       "injury",
                       "injured", "salary", "EPF", "attrition", "Dispute", "harassment", "protests", "Strike"]

    RAID_NEWS_TAG = ["Raid", "Raids", "Raided"]

    RESIGNATION_NEWS_TAG = ["Resign", "Resigns", "Resigned",
                            "Resignation", "resigning", "management changes", "terminate"]

    FRAUD_REGULATORY_ACTION_NEWS_TAG = ["Fraud", "Embezzlement",
                                        "Money laundering", "Syphoning", "CBI inquiry", "Bribery",
                                        "Political Influence", "SEBI proceeding",
                                        "regulatory action", "Penalties", "Fines", "Penalty", "Cheating", "NPA",
                                        "Default", "Criminal", "Breach",
                                        "Scam", "Arrest", "Warrant Issued", "Probe", "Fined", "Misappropriation",
                                        "Inspection", "Complaint against",
                                        "insolvency", "I T notice", "Hawala", "CBI", "FIR", "Jail", "Illeagal",
                                        "Forging", "booked", "scrutinize",
                                        "land grab", "RBI", "CBI", "SEBI", "IRDA", "EXIM", "Fraudulent", "theft",
                                        "theif", "bankruptcy",
                                        "Black Money", "Bribe", "Central Bureau of Investigation", "charge sheet",
                                        "chargesheet", "cheat",
                                        "corrupt", "corruption", "custody", "Due", "Dues", "evading", "Fine", "Fined",
                                        "forgery", "illegal",
                                        "Inspect", "Inspector", "investigation", "Labour Dispute", "land grab",
                                        "non compliance", "notices",
                                        "Offered Money", "Penalized", "police", "Serious Fraud", "SFIO", "violation",
                                        "Whistleblower"]

    MARKET_STOCK_MOVEMENT_NEWS_TAG = ["plunges", "Slowdown", "Delay",
                                      "Delayed", "downgrade", "downgraded", "losses", "loss", "SEBI", "profit decline",
                                      "Wind Up", "plummets",
                                      "Decline", "exits", "low", "pledge", "plummet", "SELL Recommendation",
                                      "stake sale", "stress", "suspends",
                                      "worst", "sell", "fall", "down", "drop", "falls", "sells"]

    LITIGATION_NEWS_TAG = ["Case Registered", "Court Denies",
                           "Court Rejects", "contempt", "Registered Case", "Settlement", "allegations", "High Court",
                           "District Court",
                           "Lower Court", "Supreme Court", "Judgement", "copyrights", "defamation", "DRT", "NCLT"]

    WHISTLEBLOWER_NEWS_TAG = ["Whistleblower"]

    ACCIDENT_NEWS_TAG = ["Accident", "Fire", "Death", "Died",
                         "Passed Away", "Die", "casualty", "mishap", "Blast", "casualties", "Died", "killed", "kills",
                         "passes away",
                         "shut down"]

    # Combine all lists into a single list
    all_tags = (LABOUR_NEWS_TAG + RAID_NEWS_TAG + RESIGNATION_NEWS_TAG + FRAUD_REGULATORY_ACTION_NEWS_TAG +
                MARKET_STOCK_MOVEMENT_NEWS_TAG + LITIGATION_NEWS_TAG + WHISTLEBLOWER_NEWS_TAG + ACCIDENT_NEWS_TAG)

    # Print the combined list
    # print(all_tags)

    # load cins of companies
    comp_cins = pd.read_excel(r'I:\NewsData\company_cin_symbol.xlsx')
    # Load News model
    # NER_sm = spacy.load("en_core_web_sm")
    NER = spacy.load("en_core_web_lg")

    # Load CSV file into a DataFrame
    csv_file_path = r'I:\NewsData\SentimentalWords.csv'  # Replace with the actual path
    df_csv = pd.read_csv(csv_file_path)

    # Map sentiment labels to numerical values
    sentiment_mapping = {'Negative': -1, 'Neutral': 0, 'Positive': 1}

    # Create a dictionary mapping words to sentiments from CSV
    word_sentiments_csv = dict(zip(df_csv['text'], df_csv['sentiment'].map(sentiment_mapping)))

    # Initialize the Sentiment Intensity Analyzer
    sia = SentimentIntensityAnalyzer()

    def get_sentence_sentiment(self, sentence):
        # Tokenize the sentence
        words = word_tokenize(sentence.lower())  # Convert to lowercase for case-insensitivity

        # Calculate the sentiment score for each word from the CSV file and aggregate
        csv_sentiment = sum(self.word_sentiments_csv.get(word, 0) for word in words)

        # Calculate the sentiment score using Sentiment Intensity Analyzer for words not found in CSV
        nlp_sentiment = self.sia.polarity_scores(sentence)['compound']

        # Combine both sentiment scores
        combined_sentiment = csv_sentiment + nlp_sentiment

        # Classify the overall sentiment based on the combined score
        if combined_sentiment > 0:
            return 'Positive'
        elif combined_sentiment < 0:
            return 'Negative'
        else:
            return 'Neutral'

    def write_to_txt(self, jsonPayload):
        file = r'I:\NewsData\news_data_push_April.txt'
        with open(file, 'a+', encoding='utf-8') as f:
            f.write(json.dumps(jsonPayload))
            f.write(",")
            f.write("\n")
            f.close()

    def spacy_large_ner(self, document):
        named_entities_set = {(ent.text.strip(), ent.label_) for ent in self.NER(document).ents}
        return [entity[0] for entity in named_entities_set if
                entity[1] == 'ORG' or entity[1] == 'PRODUCT' or entity[1] == 'PERSON']
        # return {(ent.text.strip(), ent.label_) for ent in NER(document).ents}

    def match_from_starting_word(self, str1, str2):
        # Split the strings into words
        words1 = str1.split()
        words2 = str2.split()

        # Get the minimum length of the two lists of words
        min_length = min(len(words1), len(words2))

        # Iterate through the words and check if they match
        for i in range(min_length):
            if words1[i] != words2[i]:
                return False

        return True

    def getcinfromlocal(self, input_word):
        df = pd.read_csv(r"I:\NewsData\active_cin_name_ac_pan.csv")
        cins = df['cin']
        company_names = df['company_name']
        cin_list = []
        for i, company_name in enumerate(company_names):
            if input_word.title() in company_name:
                matchresult = self.match_from_starting_word(input_word.title(), company_name)
                if matchresult:
                    cin_list.append(cins[i])
        return cin_list

    def load_company_info(self, input_word):
        symbols = comp_cins['Symbols']
        cins = comp_cins['CIN']
        subsidory_comps = comp_cins['all_subsidory_company']
        for index, symbol in enumerate(symbols):
            try:
                if input_word.title() in symbol.title() and len(input_word) == len(symbol.title()):
                    oneCin = cins[index]
                    subs = subsidory_comps[index]
                    all_comp = [item.strip() for item in subs.split(',')]

                    return all_comp
            except Exception as e:
                return []
        return []  # Return an empty list if no matching company info is found

    def get_type_tag(self, sentence):
        define_tags = (
                    self.LABOUR_NEWS_TAG + self.RAID_NEWS_TAG + self.RESIGNATION_NEWS_TAG + self.FRAUD_REGULATORY_ACTION_NEWS_TAG +
                    self.MARKET_STOCK_MOVEMENT_NEWS_TAG + self.LITIGATION_NEWS_TAG + self.WHISTLEBLOWER_NEWS_TAG + self.ACCIDENT_NEWS_TAG)

        # Tokenize the sentence into words
        tokens = word_tokenize(sentence)

        # Perform part-of-speech tagging
        tagged_words = pos_tag(tokens)

        # Extract verbs, adjectives, and adverbs based on their POS tags
        verbs = [word for word, pos in tagged_words if pos.startswith('V')]
        adjectives = [word for word, pos in tagged_words if pos.startswith('J')]
        adverbs = [word for word, pos in tagged_words if pos.startswith('R')]
        nouns = [word for word, pos in tagged_words if pos.startswith('N')]
        all_tags = (verbs + adjectives + adverbs + nouns)
        filtered_tags = [tag.title() for tag in all_tags if tag.title() in define_tags or tag in define_tags]
        if len(filtered_tags) > 0:
            return filtered_tags[0]
        return 'Other'

    def fetch_files(self, newsFiles):
        try:
            newsFile = open(newsFiles, 'r')
            for news in newsFile:
                news_payload = json.loads(
                    news.replace('},', '}').replace('\u20b9', '₹').replace('\u00a0', ' ').replace('\xa0', ' '))
                news_heading = news_payload['heading']
                news_body = news_payload['newsBody']
                if news_heading is not None:
                    type_tag = self.get_type_tag(news_heading)
                    sentiment = self.get_sentence_sentiment(news_heading)
                    comp_datas = self.spacy_large_ner(news_heading)
                    if not comp_datas:
                        comp_datas = self.spacy_large_ner(' '.join(news_body.split()[:51]))
                    if comp_datas:
                        for comp_data in comp_datas:
                            compLists = self.load_company_info(
                                comp_data.replace("'s", "").replace('\u20b9', '₹').replace('\u00a0', ' ').replace(
                                    '\xa0', ' '))
                            if not compLists and len(comp_data) > 10:
                                time.sleep(1.5)
                                compLists = self.getcinfromlocal(
                                    comp_data.replace('\u20b9', '₹').replace('\u00a0', ' ').replace('\xa0',
                                                                                                    ' ').replace('&',
                                                                                                                 'and'))
                                self.news_payload = []
                                for complist in compLists:
                                    # Append a dictionary to news_payload list without reinitializing it
                                    self.news_payload.append({
                                        "companyName": None,
                                        "cin": complist,
                                        "heading": news_heading,
                                        "typeTag": type_tag,
                                        "sentiment": sentiment,
                                        "newsDate": news_payload['newsDate'],
                                        "link": news_payload['link']
                                    })
                                if len(self.news_payload) > 0:
                                    print(json.dumps(self.news_payload))
                                    self.write_to_txt(self.news_payload)
                                    # push_news(self.news_payload)
                                    time.sleep(5)
        except Exception as e:
            print(f"Error processing news files: {str(e)}")


import os
import time

file_paths = r"I:\NewsData\NewsPayload"
previous_files = set()

while True:
    dir_list = set(os.listdir(file_paths))
    new_files = dir_list - previous_files

    # Check if there are any new files
    if new_files:
        for file in new_files:
            newsFiles = os.path.join(file_paths, file)
            NewsData().fetch_files(newsFiles)

    else:
        pass

    # Update the set of previous files for the next iteration
    previous_files = dir_list

    # Wait for 10 minutes
    time.sleep(7200)
