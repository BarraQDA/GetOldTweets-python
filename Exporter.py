# -*- coding: utf-8 -*-

import sys,getopt,got,datetime,codecs,unicodecsv

def main(argv):

	if len(argv) == 0:
		print 'You must pass some parameters. Use \"-h\" to help.'
		return

	if len(argv) == 1 and argv[0] == '-h':
		print """\nTo use this jar, you can pass the folowing attributes:
        lang: Tweet language (2 letter code)
    username: Username of a specific twitter account (without @)
       since: The lower bound date (yyyy-mm-aa)
       until: The upper bound date (yyyy-mm-aa)
 querysearch: A query text to be matched
   maxtweets: The maximum number of tweets to retrieve

 \nExamples:
 # Example 1 - Get tweets by username [barackobama]
 python Exporter.py --username "barackobama" --maxtweets 1\n

 # Example 2 - Get tweets by query search [europe refugees]
 python Exporter.py --querysearch "europe refugees" --maxtweets 1\n

 # Example 3 - Get tweets by username and bound dates [barackobama, '2015-09-10', '2015-09-12']
 python Exporter.py --username "barackobama" --since 2015-09-10 --until 2015-09-12 --maxtweets 1\n

 # Example 4 - Get the last 10 top tweets by username
 python Exporter.py --username "barackobama" --maxtweets 10 --toptweets\n"""
		return

	try:
		opts, args = getopt.getopt(argv, "", ("lang=", "username=", "since=", "until=", "querysearch=", "toptweets", "maxtweets=","outfile="))
		tweetCriteria = got.manager.TweetCriteria()

		outputFileName = "output_got.csv"

		for opt,arg in opts:
			if opt == '--username':
				tweetCriteria.username = arg

			elif opt == '--since':
				tweetCriteria.since = arg

			elif opt == '--until':
				tweetCriteria.until = arg

			elif opt == '--querysearch':
				tweetCriteria.querySearch = arg

			elif opt == '--toptweets':
				tweetCriteria.topTweets = True

			elif opt == '--maxtweets':
				tweetCriteria.maxTweets = int(arg)

			elif opt == '--lang':
				tweetCriteria.lang = arg

			elif opt == '--outfile':
				outputFileName = arg

		outputFile = codecs.open(outputFileName, "a")
		fieldnames = [ 'username', 'date', 'retweets', 'favorites', 'text', 'lang', 'geo', 'mentions', 'hashtags', 'id', 'permalink']
		# Write header row if file is empty
		if outputFile.tell() == 0:
			csvwriter=unicodecsv.DictWriter(outputFile, fieldnames=fieldnames, extrasaction='ignore')
		csvwriter.writeheader()

		print 'Searching...\n'

		def receiveBuffer(tweets):
			for t in tweets:
				csvwriter.writerow(vars(t))
			outputFile.flush()
			print 'More %d saved on file...' % len(tweets)

		got.manager.TweetManager.getTweets(tweetCriteria, receiveBuffer)

	except arg:
		print 'Arguments parser error, try -h' + arg
	finally:
		outputFile.close()
		print 'Done. Output file generated "' + outputFileName + '".'

if __name__ == '__main__':
	main(sys.argv[1:])
