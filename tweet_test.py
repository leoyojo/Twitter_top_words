import tweepy
import pandas as pd
import datetime as dt
import re
from nltk.corpus import stopwords
from collections import Counter

def remove_emojis(texto):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return re.sub(emoj, '', texto)

# Escolhe o dia em que vamos pegar os tweets
now = dt.datetime.now()
delta = now - dt.timedelta(days = 6)

pd.set_option("display.max_columns", None)

# Colocar o bearer token
bearer_token = ""

# Campos dos tweets que vamos pegar
fields = ["id","text","author_id","created_at","geo","lang","public_metrics","source"]

client = tweepy.Client(bearer_token)

# Defini a query que vamos buscar
assunto = "Will Smith lang:en"

response = client.search_recent_tweets(assunto, tweet_fields=fields, max_results=100, end_time=delta, sort_order="relevancy")
tweets = response.data

# Cria uma lista de dicionários com os tweets
lista = []
for tweet in tweets:
    dic_aux={"id": tweet["id"],
    "text": tweet["text"],
    "author_id": tweet["author_id"],
    "created_at": tweet["created_at"],
    "lang": tweet["lang"],
    "source": tweet["source"],
    "retweet_count": tweet["public_metrics"]["retweet_count"],
    "reply_count": tweet["public_metrics"]["reply_count"],
    "like_count": tweet["public_metrics"]["like_count"],
    "quote_count": tweet["public_metrics"]["quote_count"]
    }
    lista.append(dic_aux)

# Cria um DataFrame com os dados dos tweets
df = pd.DataFrame.from_dict(lista)

# Armazena todos os textos dos tweets em uma variável, e dá uma limpada nas palavras
text_complete = ""
for i in range(len(df["text"])):
    text_complete += df["text"][i] + " "
text_complete = re.sub(r"http\S+", "", text_complete)
text_complete = re.sub(r"\n", "", text_complete)
text_complete = re.sub(r"[,.!?+-;#@$%&|:()]+", "", text_complete)
text_complete = re.sub(r"[1-9]+", "", text_complete)
text_complete = remove_emojis(text_complete)

# Cria uma lista com as palavras separadas e remove as stopwords
words_to_remove = stopwords.words("english")
words_to_remove.append("Will")
words_to_remove.append("Smith")
filtered_text = [word for word in text_complete.split() if word not in words_to_remove]

# Cria um dicionário com a palavra e o número de vezes que a palavra apareceu nos tweets
word_count = dict(Counter(filtered_text))
relevant_words = {}
for key, value in word_count.items():
    if value > 1:
        relevant_words.update({key:value})

# Ordena as palavras por ordem das que mais apareceram nos tweets
relevant_words = dict(sorted(relevant_words.items(), key=lambda item: item[1], reverse=True))

print(relevant_words)

