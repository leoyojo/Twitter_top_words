import tweepy
import pandas as pd
import datetime as dt
import re
import csv
from nltk.corpus import stopwords
from nltk.metrics import distance
from collections import Counter

def remove_emojis(texto):
    """ 
    Função para remover emotes de uma string
    """
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

def ranker(word_list, tweet_text, tweet_id):
    """
    Função para rankear o texto de um tweet, dado um dicionário de palavras e pontos
    """
    pontuacao = 0
    palavras = list(set(word_list.keys()).intersection(set(tweet_text.split(" "))))
    #print(palavras)
    for word in palavras:
        pontuacao += word_list[word]
    result = {"pontuacao":pontuacao, "palavras":palavras, "id":int(tweet_id)}
    return result

def e_repetido(lista_tweets, texto):
    """
    Função para ver a probabilidade de texto ser repetido dentre os conteúdos nos tweets da lista_tweets
    """
    if len(lista_tweets) > 0:
        max_pontuacao = 0
        for itens in lista_tweets:
            pont_temp = distance.jaro_similarity(itens["text"], texto)
            if pont_temp > max_pontuacao:
                max_pontuacao = pont_temp
        return max_pontuacao
    return 0

pd.set_option("display.max_columns", None)

# Colocar o bearer token
bearer_token = ""

# Campos dos tweets que vamos pegar
fields = ["id","text","author_id","created_at","lang","source","public_metrics"]
fields_df = ["id","text","author_id","created_at","lang","source","retweet_count","reply_count","like_count","quote_count"]

client = tweepy.Client(bearer_token)

# Defini a query que vamos buscar
palavra = "sport"
query = palavra + " -is:retweet -is:reply lang:en"

# Faz um loop para para fazer vários requests de tweets com diferentes horários
for time_dif in range(10):
    # Escolhe o dia em que vamos pegar os tweets
    delta = dt.datetime.now() - dt.timedelta(days = 6, hours = time_dif)

    # Pega os tweets
    response = client.search_recent_tweets(query, tweet_fields=fields, max_results=100, end_time=delta, sort_order="relevancy")
    tweets = response.data

    # Cria uma lista de dicionários com os tweets, caso o texto do tweet não seja repetido
    lista = []
    for tweet in tweets:
        if e_repetido(lista, tweet.text) < 0.9:
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

    # Salva a lista de tweets em um arquivo
    with open("tweets.csv", "a", encoding="utf-8") as csvfile:
        csvfile.write("\n")
        dict_writer = csv.DictWriter(csvfile, fields_df)
        dict_writer.writerows(lista)

# Cria um DataFrame com os dados dos tweets
#df = pd.DataFrame.from_dict(lista)
df = pd.read_csv("tweets.csv")

# Armazena todos os textos dos tweets em uma variável, e dá uma limpada nas palavras
text_complete = ""
for i in range(len(df["text"])):
    text_complete += df["text"][i] + " "
text_complete = re.sub(r"http\S+", "", text_complete)
text_complete = re.sub(r"\n", "", text_complete)
text_complete = re.sub(r"[,.!?+-;#@$%&–|:_()'\[\]\}\{}]+", "", text_complete)
text_complete = re.sub(r"[1-9]+", "", text_complete)
text_complete = remove_emojis(text_complete)
text_complete = text_complete.lower()

# Cria uma lista com as palavras separadas e remove as stopwords
words_to_remove = stopwords.words("english")
words_to_remove.append(palavra)
filtered_text = [word for word in text_complete.split() if word not in words_to_remove]

# Cria um dicionário com a palavra e o número de vezes que a palavra apareceu nos tweets
word_count = dict(Counter(filtered_text))
relevant_words = {}
for key, value in word_count.items():
    if value > 1:
        relevant_words.update({key:value})

# Ordena as palavras por ordem das que mais apareceram nos tweets e printa a lista dessas palavras
relevant_words = dict(sorted(relevant_words.items(), key=lambda item: item[1], reverse=True))
print(relevant_words)

# Aplica a função de ranqueamento na coluna de texto dos tweets
dict_aux = df.apply(lambda x: ranker(relevant_words, x["text"], x["id"]), axis=1)

# Junta o resultado do ranqueamento dos tweets no dataframe do tweets
df_final = df.merge(pd.DataFrame.from_dict(list(dict_aux)), on="id")
df_final = df_final.drop_duplicates(subset="id")

# Printa os tweets em ordem de maior pontuação e salva em um arquivo
print(df_final.sort_values("pontuacao", ascending=False).head(10))
df_final.to_csv("resultado.csv")