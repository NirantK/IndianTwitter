import re

import emoji
import spacy
import string
import wordcloud

import config


def replace(txt, chars=['\n', '\t', '\r', '\v'], replacement=' @-@ '):
    for char in chars:
        txt = txt.replace(char, replacement)
    return txt

def is_coordinate(string):
	if ':' in string:
		string = string[string.find(':') + 1:].strip()
	return re.match('^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$', string) is not None, string

def get_stopwords(sub='bios'):
	nlp = spacy.load('en_core_web_sm')
	stopwords = spacy.lang.en.stop_words.STOP_WORDS | set(wordcloud.STOPWORDS)
	locs = ['bay', 'area', 'los', 'angeles', 'la', 'sf', 'san', 'francisco', 'ma',
			'new', 'york', 'nyc', 'ny', 'london', 'silicon', 'valley', 'uk', 'tx',
			'california', 'dc', 'seattle', 'atlanta', 'sydney', 'toronto', 'canada',
			'usa', 'toronto', 'chicago', 'ontario', 'austin', 'texas', 'britain',
			'washington', 'jose', 'oakland', 'georgia', 'ca', 'ga', 'illinois', 'il',
			'wa', 'australia', 'us', 'au', 'england', 'en', 'melbourne', 'atl', 'boston',
			'long', 'island', 'upstate', 'brooklyn', 'palo', 'alto', 'redwood', 'city',
			'bayarea', 'losangeles', 'atx', 'irvine', 'amp', 'sanfrancisco', 'bit', 'ly', 'queens',
			'pasadena', 'malibu', 'va', 'berkeley', 'syracuse', 'sanjose', 'clara', 'monica',
			'l.a', 'sj', 'aus', 'u.s']
	
	stopwords = stopwords | set(locs)

	for word in ['co', 'https', 'thing', "'s", "'d", "'m", 'things', 'con', 'und', 'nt', "n't", 'rt',
				'del', 'de', 'el', 'soy', 'mi', 'las', 'la', 'yo', 'que', 'por', 'quien',
				'll', "y'", 'ye', 'unk', '<unk>', 'gon', 'na', 'gonna', 'url', '<url>', "w/"]:
		stopwords.add(word)

	for word in ['—', '@-@', '//', '...', '•', '…', '....']:
		stopwords.add(word)

	for word in string.punctuation:
		stopwords.add(word)


	numbers = set([str(i) for i in range(1000)])
	stopwords = stopwords | numbers

	numbers = set([str(i) for i in range(1960, 2020)])
	stopwords = stopwords | numbers

	if sub == 'tweets':
		for word in ['thank', 'thanks', 've', 'today', 'day', 'night', 'time', 'people', 'year',
					'week', 'love', 'know', 'need', 'want', 'think', 'good', 'great',
					'tonight', 'right', 'way', 'look', 'check', 'tweet', 'let', 'twitter',
					'mean', 'morning', 'oh', 'yes', 'sure', 'going', 'come', 'live', 'life',
					'find', 'guy', 'gonna', 'love', 'best', 'better', 'hey']:
			stopwords.add(word)

	return stopwords

def load_vocab(file, threshold=3):
	lines = open(file, 'r').readlines()
	vocab = {}
	for line in lines:
		word, c = line[:-1].split('\t')
		c = int(c)
		if c < threshold:
			break
		vocab[word] = c
	return vocab

def compare_vocabs(vocab1, vocab2, city1, city2, thres1, thres2, at_least_ratio=2):
	unique1, unique2 = {}, {}
	strong1, strong2 = {}, {}
	ratios = {}
	total1 = sum(vocab1.values())
	total2 = sum(vocab2.values())
	
	results1, results2 = {}, {}

	for word in vocab1:
		if not word in vocab2:
			unique1[word] = vocab1[word]
		else:
			rat1 = vocab1[word] / total1
			rat2 = vocab2[word] / total2
			ratios[word] = rat1 / rat2

	for word in vocab2:
		if not word in vocab1:
			unique2[word] = vocab2[word]

	for w in sorted(unique1, key=unique1.get, reverse=True):
		if vocab1[w] < thres1:
			break
		results1[w] = vocab1[w] / total1

	for w in sorted(ratios, key=ratios.get, reverse=True):
		if vocab1[w] < thres1:
			break
		if ratios[w] < at_least_ratio:
			continue
		diff = (vocab1[w] / total1) - (vocab2[w] / total2)
		if diff <= 0:
			break
		results1[w] = diff

	for w in sorted(unique2, key=unique2.get, reverse=True):
		if vocab2[w] < thres2:
			break
		results2[w] = vocab2[w] / total2

	for w in sorted(ratios, key=ratios.get, reverse=False):
		if vocab2[w] < thres2:
			break
		if ratios[w] > 1 / at_least_ratio:
			break
		diff = vocab2[w] / total2 - vocab1[w] / total1
		if diff <= 0:
			break
		results2[w] = diff

	return results1, results2

def is_printable(word):
	for c in word:
		if not c in string.printable:
			return False
	return True

def filter_stopwords(frequencies, stopwords, filter_unprintable=True):
	results = {}
	for key in frequencies:
		if not key.lower() in stopwords:
			if not filter_unprintable:
				results[key] = frequencies[key]
			else:
				if is_printable(key) and not key.lower() in emoji.UNICODE_EMOJI:
					results[key] = frequencies[key]
	return results

def get_threshold(sub, city1, city2):
	if sub == 'tweets':
		if city1 == 'other':
			return 40, 20
		if city2 == 'other':
			return 20, 40
		return 40, 40
	else:
		thres1 = config.THRES[city1]
		thres2 = config.THRES[city2]
		if city1 == 'other' and thres2 > 8:
			return thres1, thres2-3
		if city2 == 'other' and thres1 > 8:
			return thres1-3, thres2
		return thres1, thres2

