import re
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words('english'))
TKNZR = TweetTokenizer()

def remove_url(txt):
	"""Replace URLs found in a text string with nothing 
	(i.e. it will remove the URL from the string).

	Parameters
	----------
	txt : string
		A text string that you want to parse and remove urls.

	Returns
	-------
	The same txt string with url's removed.
	"""

	return " ".join(re.sub("([^0-9A-Za-z \t])|(\w+:\/\/\S+)", "", txt).split())

def tweet_toks(tweet):
	tweet = remove_url(tweet.lower())
	tweet_words = TKNZR.tokenize(tweet)
	tweet_words = [x for x in tweet_words if x not in STOPWORDS]

	return tweet_words
