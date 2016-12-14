import urllib,urllib2,json,re,datetime,sys,cookielib
from .. import models
from pyquery import PyQuery

class TweetManager:

	def __init__(self):
		pass

	@staticmethod
	def getTweets(tweetCriteria, receiveBuffer = None, bufferLength = 100, lastid = None):
		refreshCursor = ''

		results = []
		resultsAux = []
		cookieJar = cookielib.CookieJar()

		if hasattr(tweetCriteria, 'username') and (tweetCriteria.username.startswith("\'") or tweetCriteria.username.startswith("\"")) and (tweetCriteria.username.endswith("\'") or tweetCriteria.username.endswith("\"")):
			tweetCriteria.username = tweetCriteria.username[1:-1]

		active = True
		freshtweets = False
		dateSec = None
		abortAfter = 2
		abortCount = 0

		overlap = True

		while active:
			json = TweetManager.getJsonReponse(tweetCriteria, refreshCursor, cookieJar)

			tweets = None
			if json is not None and len(json['items_html'].strip()) > 0:
				refreshCursor = json['min_position']
				tweets = PyQuery(json['items_html'])('div.js-stream-tweet')

			if tweets is None or len(tweets) == 0:
				if not freshtweets or dateSec is None:
					abortCount += 1
					if abortCount == abortAfter:
						break
					print "Retrying..."

				freshtweets = False
				# Set 'until' criterion to date of last retrieved tweet
				if dateSec is not None:
					tweetCriteria.until = (datetime.datetime.utcfromtimestamp(dateSec) + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
					print "Setting until criteria to " + tweetCriteria.until

				refreshCursor = ''
				overlap = False
				continue

			for tweetHTML in tweets:
				tweetPQ = PyQuery(tweetHTML)

				# Get timestamp to help resume
				dateSec = int(tweetPQ("small.time span.js-short-timestamp").attr("data-time"));

				# Skip retweets
				retweet = tweetPQ("span.js-retweet-text").text()
				if retweet != '':
					continue

				# Ignore non-descending tweet IDs. This can happen when we do a restart
				# following search exhaustion.
				id = tweetPQ.attr("data-tweet-id");
				if lastid is not None and id >= lastid:
					overlap = True
					if freshtweets:
						raise "Out of order tweets!"

					continue

				freshtweets = True
				abortCount = 0

				if not overlap:
					# Add an empty tweet to signal possible missing tweets
					resultsAux.append(models.Tweet())

				usernameTweet = tweetPQ("span.username.js-action-profile-name b").text();
				lang = tweetPQ("p.js-tweet-text").attr("lang")
				txt = re.sub(r"\s+", " ", tweetPQ("p.js-tweet-text").text().replace('# ', '#').replace('@ ', '@'));
				retweets = int(tweetPQ("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""));
				favorites = int(tweetPQ("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""));
				permalink = tweetPQ.attr("data-permalink-path");

				geo = ''
				geoSpan = tweetPQ('span.Tweet-geo')
				if len(geoSpan) > 0:
					geo = geoSpan.attr('title')

				tweet = models.Tweet()
				tweet.id = id
				tweet.lang = lang
				tweet.permalink = 'https://twitter.com' + permalink
				tweet.username = usernameTweet
				tweet.text = txt
				tweet.date = datetime.datetime.fromtimestamp(dateSec)
				tweet.retweets = retweets
				tweet.favorites = favorites
				tweet.mentions = " ".join(re.compile('(@\\w*)').findall(tweet.text))
				tweet.hashtags = " ".join(re.compile('(#\\w*)').findall(tweet.text))
				tweet.geo = geo

				results.append(tweet)
				resultsAux.append(tweet)

				lastid = id

				if receiveBuffer and len(resultsAux) >= bufferLength:
					receiveBuffer(resultsAux)
					resultsAux = []

				if tweetCriteria.maxTweets > 0 and len(results) >= tweetCriteria.maxTweets:
					active = False
					break


		if receiveBuffer and len(resultsAux) > 0:
			receiveBuffer(resultsAux)

		return results

	@staticmethod
	def getJsonReponse(tweetCriteria, refreshCursor, cookieJar):
		url = "https://twitter.com/i/search/timeline?f=tweets&q=%s&src=typd&max_position=%s"

		urlGetData = ''
		if hasattr(tweetCriteria, 'lang'):
			urlGetData += ' lang:' + tweetCriteria.lang

		if hasattr(tweetCriteria, 'username'):
			urlGetData += ' from:' + tweetCriteria.username

		if hasattr(tweetCriteria, 'since'):
			urlGetData += ' since:' + tweetCriteria.since

		if hasattr(tweetCriteria, 'until'):
			urlGetData += ' until:' + tweetCriteria.until

		if hasattr(tweetCriteria, 'querySearch'):
			urlGetData += ' ' + tweetCriteria.querySearch

		if hasattr(tweetCriteria, 'topTweets'):
			if tweetCriteria.topTweets:
				url = "https://twitter.com/i/search/timeline?q=%s&src=typd&max_position=%s"

		#print "Cursor: " + refreshCursor
		url = url % (urllib.quote(urlGetData), refreshCursor)

		headers = [
			('Host', "twitter.com"),
			('User-Agent', "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"),
			('Accept', "application/json, text/javascript, */*; q=0.01"),
			('Accept-Language', "de,en-US;q=0.7,en;q=0.3"),
			('X-Requested-With', "XMLHttpRequest"),
			('Referer', url),
			('Connection', "keep-alive")
		]

		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
		opener.addheaders = headers

		try:
			response = opener.open(url)
			jsonResponse = response.read()
			print "Read response to: " + url
		except:
			print "Twitter weird response. Try to see on browser: " + url
			#sys.exit()
			return None

		dataJson = json.loads(jsonResponse)
		return dataJson
