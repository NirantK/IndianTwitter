from datetime import datetime
import glob, os
import random
import string

import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import numpy as np
import spacy

import config
import utils


def clean_url():
	import re
	sub = 'tweets'
	infold = 'small/tokenized/' + sub
	outfold = 'small/tokenized/clean_' + sub
	os.makedirs(outfold, exist_ok=True)

	files = glob.glob(infold + '/*.tok')
	for file in files:
		filename = file[file.rfind('/')+1:]
		out = open(os.path.join(outfold, filename), 'w')
		with open(file, 'r') as f:
			for line in f:
				line = re.sub(r'http\S+|www.\S+', '<url>', line)
				out.write(line)
		out.close()

def tokenize_file(infile, outfile, nlp, idx=-1):
	out = open(outfile, 'w')
	i = 0
	with open(infile, 'r') as f:
		for line in f:
			bio = line.strip().lower().split('\t')[-1]
			doc = nlp(bio)
			txt = ' '.join([token.text for token in doc])
			out.write(txt + '\n')
			i += 1
			if i % 1000 == 0:
				print(i)
	out.close()

def tokenize_bios():
	nlp = spacy.load('en_core_web_lg')
	outfold = 'processed/tokenized/bios'
	os.makedirs(outfold, exist_ok=True)
	for city in ['austin']:
		print('-' * 30 + city)
		infile = 'data/' + city + '.users'
		outfile = os.path.join(outfold, city + '.tok')
		tokenize_file(infile, outfile, nlp)

def tokenize_tweets():
	nlp = spacy.load('en_core_web_lg')
	outfold = 'processed/tokenized/all_tweets'
	os.makedirs(outfold, exist_ok=True)
	users = glob.glob('tweets/T*.csv')
	for userfile in users:
		username = userfile[7:-4]
		outfile = os.path.join(outfold, username + '.tok')
		if os.path.isfile(outfile):
			print('Skip', username)
			continue
		print(userfile)
		tokenize_file(userfile, outfile, nlp)

def get_users_by_city(city):
	users = set()
	with open('data/{}.users'.format(city), 'r') as f:
		for line in f:
			users.add(line.strip().split('\t')[0])
	return users

def get_tweets_by_city():
	outfold = 'processed/tokenized/tweets'
	os.makedirs(outfold, exist_ok=True)
	infold = 'processed/tokenized/all_tweets'

	# for city in config.CITIES:
	austin_users = set(get_users_by_city('austin'))
	for city in ['other']:
		out = open('{}/{}.tok'.format(outfold, city), 'w')
		users = get_users_by_city(city)
		
		if city == 'other':
			ratio = 0.5
		else:
			ratio = 1

		for user in users:
			if city == 'other' and user in austin_users:
				continue

			if random.random() < ratio:
				file = '{}/{}.tok'.format(infold, user)
				if os.path.isfile(file):
					with open(file, 'r') as f:
						out.write(f.read())
		
		out.close()

def remove_stopwords(sub, d='processed'):
	nlp = spacy.load('en_core_web_sm')
	stopwords = utils.get_stopwords()

	infold = d + '/tokenized'
	outfold = d + '/cleaned'

	subinfold = os.path.join(infold, sub)
	suboutfold = os.path.join(outfold, sub)
	os.makedirs(suboutfold, exist_ok=True)

	files = glob.glob(subinfold + '/*.tok')
	for file in files:
		filename = file[file.rfind('/')+1:]

		out = open(os.path.join(suboutfold, filename), 'w')
		with open(file, 'r') as f:
			for line in f:
				line = line.strip().replace("’", "'")
				line = line.replace("’", "'")
				line = line.replace("“", '"')
				line = line.replace('”', '"')
				raw_tokens = line.split()
				tokens = [token for token in raw_tokens if len(token) > 0 and not token.lower() in stopwords]
				if len(tokens) > 0:
					out.write(' '.join(tokens) + '\n')

		out.close()

def stem(sub, d='processed'):
	from nltk.stem.snowball import SnowballStemmer
	stemmer = SnowballStemmer(language='english')
	infold = d + '/cleaned'
	outfold = d + '/stemmed'

	subinfold = os.path.join(infold, sub)
	suboutfold = os.path.join(outfold, sub)
	os.makedirs(suboutfold, exist_ok=True)

	files = glob.glob(subinfold + '/*.tok')
	for file in files:
		filename = file[file.rfind('/')+1:]

		out = open(os.path.join(suboutfold, filename), 'w')
		with open(file, 'r') as f:
			for line in f:
				line = line.strip().replace("’", "'")
				raw_tokens = line.split()
				tokens = [stemmer.stem(token) for token in raw_tokens if len(token) > 1]
				if len(tokens) > 0:
					out.write(' '.join(tokens) + '\n')
		out.close()

def get_weekday(date):
	year, month, day = date.split('-')
	if month[0] == 0:
		month = month[1:]
	return config.NUM2DATES[datetime(int(year), int(month), int(day)).weekday()]

def get_pop_by_dates():
	infold = 'tweets'
	outfold = 'processed/dates'
	os.makedirs(outfold, exist_ok=True)

	for city in config.CITIES:
		out = open('{}/{}.csv'.format(outfold, city), 'w')
		out.write('\t'.join(['date', 'day', 'time', 'retweet', 'favorite']) + '\n')
		users = get_users_by_city(city)
		for user in users:
			file = '{}/{}.csv'.format(infold, user)
			if os.path.isfile(file):
				with open(file, 'r') as f:
					for line in f:
						parts = line.strip().split('\t')
						date, time = parts[1].split()
						day = get_weekday(date)
						out.write('\t'.join([date, day, time, parts[2], parts[3]]) + '\n')
		out.close()

def find_most_common_cities():
	tokens = []
	with open(os.path.join(outfold, 'other.users'), 'r') as f:
		for line in f:
			loc = line.strip().split('\t')[1].lower()
			doc = nlp(loc)
			for token in doc:
			    tokens.append(token.text)

	with open(os.path.join(outfold, 'loc.vocab'), 'w') as f:
		for token, c in Counter(tokens).most_common():
			f.write('{}\t{}\n'.format(token, c))


def build_vocab_city(city, tok='cleaned'):
	tokens = []
	
	with open(os.path.join(d, tok, sub, city + '.tok'), 'r') as f:
		for line in f:
			line = line.strip()
			if line:
				tokens.extend(line.split(' '))

	with open(os.path.join(outfold, city + '.vocab'), 'w') as f:
		for token, c in Counter(tokens).most_common():
			f.write('{}\t{}\n'.format(token, c))
	
def combine_vocab():
	vocab = Counter()
	for city in config.CITIES:
		tmp = utils.load_vocab(os.path.join(outfold,  city + '.vocab'), threshold=1)
		vocab = vocab + Counter(tmp)

	with open(os.path.join(outfold,  'other.vocab'), 'w') as f:
		for token, c in vocab.most_common():
			f.write('{}\t{}\n'.format(token, c))
	return vocab

def build_vocab():
	for city in config.CITIES:
		print(city)
		build_vocab_city(city)


def build_vocab_cities():
	build_vocab()
	if sub == 'bios':
		build_vocab_city('other')
	else:
		combine_vocab()
		print('done combining')

def filter_vocabs(sub):
	if sub == 'bios':
		threshold = 2
	else:
		threshold = 6
	infold = 'vocabs_full/{}'.format(sub)
	outfold = 'vocabs/{}'.format(sub)
	os.makedirs(outfold, exist_ok=True)

	unk = 0

	for city in config.CITIES + ['other']:
		out = open(os.path.join(outfold, city + '.vocab'), 'w')
		with open(os.path.join(infold, city + '.vocab'), 'r') as f:

			for line in f:
				count = int(line.strip().split('\t')[-1])
				if count < threshold:
					unk += 1
				else:
					out.write(line)
		out.write('<unk>\t{}\n'.format(unk))
		out.close()

def subsample(sub, n=2000000):
	infold = os.path.join('processed', sub, 'tweets')
	outfold = os.path.join('small_2m', sub, 'tweets')
	os.makedirs(outfold, exist_ok=True)

	for city in config.CITIES + ['other']:
		ratio = n / config.TWEETS_COUNT[city]
		if ratio >= 1:
			print(city)
			continue
		out = open(os.path.join(outfold, city + '.tok'), 'w')

		with open(os.path.join(infold, city + '.tok'), 'r') as f:
			for line in f:
				if random.random() < ratio:
					out.write(line)

		out.close()

def clean_unprintable(infold, outfold, to_replace={"’": "'", "’": "'", "“": '"', '”': '"', "…": "...", "—": '-', '‘': "'", "–": '-'}):
	os.makedirs(outfold, exist_ok=True)
	files = glob.glob(infold + '/*.vocab')
	
	for file in files:
		filename = file[file.rfind('/')+1:]
		out = open(os.path.join(outfold, filename), 'w')
		vocabs = {}
		with open(file, 'r') as f:
			for line in f:
				parts = line.strip().split('\t')
				if len(parts) < 2:
					continue
				word, count = parts[0], int(parts[1])
				for char in to_replace: 
					word = word.replace(char, to_replace[char])
				if not word in vocabs:
					vocabs[word] = count
				else:
					vocabs[word] += count

		for key in sorted(vocabs, key=vocabs.get, reverse=True):
			out.write('{}\t{}\n'.format(key, vocabs[key]))
		out.close()

clean_unprintable('raw_vocabs/tweets', 'vocabs/tweets')

