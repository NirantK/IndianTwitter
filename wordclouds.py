from collections import Counter
import os
import random

import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import spacy
from wordcloud import STOPWORDS, WordCloud

import config
import utils


TITLE_TMP = {
	'tweets': 'WHAT PEOPLE IN {} TALK ABOUT',
	'bios': 'HOW PEOPLE IN {} DESCRIBE THEMSELVES'
}


def create_text_wc(results):
	if len(results) > 300:
		new_results = {}
		for w in sorted(results, key=results.get, reverse=True)[:300]:
			new_results[w] = results[w]
		del results
		results = new_results

	min_ = min(results.values())
	factor = 1 / min_
	tokens = []

	i = 0
	for w in results:
		tokens.extend([w] * int(factor * results[w]))
		i += 1
		if i % 5 == 0:
			random.shuffle(tokens)
	random.shuffle(tokens)
	txt = ' '.join(tokens)
	return txt

def create_duo_word_clouds_helper(outfold, sub, text1, city1, text2, city2, stopwords):
	cloud1 = WordCloud(stopwords=stopwords, background_color="white").generate(text1)
	cloud2 = WordCloud(stopwords=stopwords, background_color="white").generate(text2)

	if city1 == 'other':
		title1 = title.format(city1.upper())
	fig = plt.figure(figsize=(15, 15))
	fig.add_subplot(2, 1, 1)
	plt.imshow(cloud1, interpolation='bilinear')
	plt.axis("off")
	# plt.title(get_title(sub, city1), fontsize=25, color='r')
	plt.title(city1.upper(), fontsize=25, fontweight='black', color='r')
	fig.add_subplot(2, 1, 2)
	plt.imshow(cloud2, interpolation='bilinear')
	plt.axis("off")
	# plt.title(get_title(sub, city2), fontsize=25, color='g')
	plt.title(city2.upper(), fontsize=25, fontweight='black', color='g')
	plt.savefig('{}/{}_{}'.format(outfold, city1, city2))
	plt.clf()
	plt.close()


def create_duo_word_clouds(infold, outfold, sub, city1, city2, stopwords):
	vocab1 = utils.load_vocab('vocabs/{}/{}.vocab'.format(sub, city1), 3)
	vocab2 = utils.load_vocab('vocabs/{}/{}.vocab'.format(sub, city2), 3)
	
	thres1, thres2 = utils.get_threshold(sub, city1, city2)
	results1, results2 = utils.compare_vocabs(vocab1, vocab2, city1, city2, thres1, thres2)
	text1 = create_text_wc(results1)
	text2 = create_text_wc(results2)

	# frequencies1 = utils.filter_stopwords(results1, stopwords, filter_unprintable=True)
	# frequencies2 = utils.filter_stopwords(results2, stopwords, filter_unprintable=True)
	create_duo_word_clouds_helper(outfold, sub, text1, city1, text2, city2, stopwords)

def create_all_duo_word_clouds(infold, outfold, sub):
	stopwords = utils.get_stopwords(sub)
	outfold = os.path.join(outfold, sub, 'duo')
	os.makedirs(outfold, exist_ok=True)

	# for i, city1 in enumerate(config.CITIES + ['other']):
	# 	for j, city2 in enumerate(config.CITIES + ['other']):

	stopwords.add('favorite')
	stopwords.add('favourite')
	stopwords.add('mom')
	stopwords.add('mum')
	for i, city1 in enumerate(['nyc']):
		for j, city2 in enumerate(['melbourne']):
			if i <= j:
				create_duo_word_clouds(infold, outfold, sub, city1, city2, stopwords)

def get_title(sub, city):
	if city == 'other':
		return TITLE_TMP[sub].format('IN OTHER PARTS')
	return TITLE_TMP[sub].format(city.upper()) 

def create_indi_word_cloud(infold, outfold, sub, city, stopwords):
	text = ''
	with open(os.path.join(infold, sub, city + '.tok'), 'r') as f:
		for line in f:
			text += line
	
	cloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)

	fig = plt.figure(figsize=(10, 5))
	plt.imshow(cloud, interpolation='bilinear')
	plt.axis("off")
	plt.title(get_title(sub, city), fontsize=10, color='g')
	plt.savefig('{}/{}'.format(outfold, city))
	plt.clf()
	plt.close()

def create_all_indi_word_clouds(infold, outfold, sub='tweets'):
	stopwords = utils.get_stopwords(sub)
	outfold = os.path.join(outfold, sub, 'indi')
	os.makedirs(outfold, exist_ok=True)
	for i, city in enumerate(config.CITIES + ['other']):
		print(city)
		create_indi_word_cloud(infold, outfold, sub, city, stopwords)


# create_all_indi_word_clouds('not_use/cleaned', 'images', 'tweets')
create_all_duo_word_clouds('vocabs', 'images', 'bios')
