from collections import Counter
import os

import emoji
import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import numpy as np
import wordcloud

import config
import utils

def get_year_distribution():
    outfold = 'images/year'
    os.makedirs(outfold, exist_ok=True)

    years = {}
    for city in config.CITIES:
        with open('processed/dates/{}.csv'.format(city), 'r') as f:
            f.readline()
            for line in f:
                year = int(line.strip().split('\t')[0].split('-')[0])
                if not year in years:
                    years[year] = 0
                years[year] += 1

        y_pos = [i for i in range(len(years))]
        keys, values = [], []
        total = sum(years.values())
        for year, count in sorted(years.items()):
            keys.append(year)
            values.append(100 * count / total)
        pretty_barplot(y_pos, values, keys, 'Percentage', 'TWEETS BY YEAR IN ' + city.upper(), os.path.join(outfold, city))

def add_values(base_values, idx, values_to_add):
    for kw in values_to_add:
        base_values[kw][idx] += values_to_add[kw]
    return base_values

def get_popuplarity_distribution(outfold):
    os.makedirs(outfold + '/hour', exist_ok=True)
    os.makedirs(outfold + '/day', exist_ok=True)

    colors = {'rt': 'deeppink', 'fav': 'limegreen', 'tweet': 'lightskyblue'}

    ticks = {'hour': ('12am', '3am', '6am', '9am', '12pm', '3pm', '6pm', '9pm'),
             'day': ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')}
    
    keywords = ['tweet', 'rt', 'fav']
    
    n = {'hour': 24, 'day': 7}
    n_step = {'hour': 3, 'day': 1}

    modes = ['hour', 'day']
    
    values, x_values = {}, {}
    values_weekend = {kw: [0 for _ in range(24)] for kw in keywords}
    values_weekday = {kw: [0 for _ in range(24)] for kw in keywords}
    
    for mode in modes:
        values[mode] = {kw: [0 for _ in range(n[mode])] for kw in keywords}
        x_values[mode] = [i for i in range(n[mode])]

    for city in config.CITIES:
        print(city)
        with open('processed/dates/{}.csv'.format(city), 'r') as f:
            f.readline()
            for line in f:
                current_values = {}
                parts = line.strip().split('\t')
                hour = int(parts[2].split(':')[0]) + config.TIMEZONES[city]
                day = config.DATES2NUM[parts[1]]
                if hour < 0:
                    day -= 1
                if hour > 23:
                    day -= 1
                current_values['hour'] = hour % 24
                current_values['day'] = day % 7

                for mode in modes:
                    values[mode] = add_values(values[mode], current_values[mode], 
                                    {'tweet': 1, 'rt': int(parts[-2]), 'fav': int(parts[-1])})

                    if mode == 'hour':
                        if day < 5:
                            values_weekday = add_values(values_weekday, current_values[mode], 
                                                {'tweet': 1, 'rt': int(parts[-2]), 'fav': int(parts[-1])})
                        else:
                            values_weekend = add_values(values_weekend, current_values[mode],
                                                {'tweet': 1, 'rt': int(parts[-2]), 'fav': int(parts[-1])})

        for mode in modes:
            fig = plt.figure(figsize=(10, 5))
            for kw in ['rt', 'fav', 'tweet']:
                total = sum(values[mode][kw])
                for value in x_values[mode]:
                    values[mode][kw][value] = 100 * values[mode][kw][value]  / total
                plt.plot(x_values[mode], values[mode][kw], ls='-', color=colors[kw])
            
            plt.legend(['retweet', 'favorite', 'tweet'], loc='upper left')

            plt.ylabel('Percentage')
            plt.xticks(np.arange(0, n[mode], step=n_step[mode]), ticks[mode])
            plt.title(city.upper())
            plt.savefig(os.path.join(outfold, mode, city))
            plt.clf()

            if mode == 'hour':
                fig = plt.figure(figsize=(10, 5))
                for kw in ['rt', 'fav', 'tweet']:
                    total = sum(values_weekday[kw])
                    for value in x_values[mode]:
                        values_weekday[kw][value] = 100 * values_weekday[kw][value]  / total
                    plt.plot(x_values[mode], values_weekday[kw], ls=':', color=colors[kw])

                for kw in ['rt', 'fav', 'tweet']:
                    total = sum(values_weekend[kw])
                    for value in x_values[mode]:
                        values_weekend[kw][value] = 100 * values_weekend[kw][value]  / total
                    plt.plot(x_values[mode], values_weekend[kw], ls='-', color=colors[kw])
            
                plt.legend(['retweet (weekday)', 'favorite (weekday)', 'tweet (weekday)',
                            'retweet (weekend)', 'favorite (weekend)', 'tweet (weekend)'], 
                           loc='upper left')

                plt.ylabel('Percentage')
                plt.xticks(np.arange(0, n[mode], step=n_step[mode]), ticks[mode])
                plt.title(city.upper())
                plt.savefig(os.path.join(outfold, mode, city + '_sep'))
                plt.clf()


        for mode in modes:
            normalized_values = {kw: [0 for _ in range(n[mode])] for kw in ['rt', 'fav']}
            
            fig = plt.figure(figsize=(10, 5))
            
            for kw in ['rt', 'fav']:
                for value in x_values[mode]:
                    normalized_values[kw][value] = values[mode][kw][value] / values[mode]['tweet'][value]
                plt.plot(x_values[mode], normalized_values[kw], ls='-', color=colors[kw])

            plt.legend(['retweet', 'favorite'], loc='upper left')
            plt.ylabel('Count per tweet')
            plt.xticks(np.arange(0, n[mode], step=n_step[mode]), ticks[mode])
            plt.title(city.upper())
            plt.savefig(os.path.join(outfold, mode, city + '_per_tweet'))
            plt.clf()

            if mode == 'hour':
                for kw in ['rt', 'fav']:
                    for value in x_values[mode]:
                        normalized_values[kw][value] = values_weekday[kw][value] / values_weekday['tweet'][value]
                    plt.plot(x_values[mode], normalized_values[kw], ls=':', color=colors[kw])

                for kw in ['rt', 'fav']:
                    for value in x_values[mode]:
                        normalized_values[kw][value] = values_weekend[kw][value] / values_weekend['tweet'][value]
                    plt.plot(x_values[mode], normalized_values[kw], ls='-', color=colors[kw])

                plt.legend(['retweet (weekday)', 'favorite (weekday)',
                            'retweet (weekend)', 'favorite (weekend)',], 
                           loc='upper left')

                plt.ylabel('Count per tweet')
                plt.xticks(np.arange(0, n[mode], step=n_step[mode]), ticks[mode])
                plt.title(city.upper())
                plt.savefig(os.path.join(outfold, mode, city + '_per_tweet_sep'))
                plt.clf()

def pretty_barplot(y_pos, values, objects, xlabel, title, outfile):
    fig = plt.figure(figsize=(10, 6))
    plt.rcParams['axes.edgecolor']='#333F4B'
    plt.rcParams['axes.linewidth']=0.8
    plt.rcParams['xtick.color']='#333F4B'
    plt.rcParams['ytick.color']='#333F4B'

    plt.barh(y_pos, values, align='center', color='#007acc', alpha=0.6)
    plt.yticks(y_pos, objects)
    plt.xlabel(xlabel, fontsize=8, fontweight='black', color='#333F4B')
    plt.title(title, fontsize=15, fontweight='black', color='#333F4B')

    plt.savefig(outfile)
    plt.clf()

def get_diff_vocabs(city_vocab, other_vocab, city, other, thres1, thres2, at_least_ratio, results):
    print(city.upper())

    results1, results2 = utils.compare_vocabs(city_vocab, other_vocab, city, other, thres1, thres2, at_least_ratio)
    emojis = []

    for key, value in sorted(results1.items(), reverse=True): # True is descending order
        if key in emoji.UNICODE_EMOJI:
            emojis.append(key)

    print(''.join(emojis))

    if results == 1:
        return sum(results1.values()) * 100
    if results == 2:
    	   return sum(results2.values()) * 100
    return (sum(results1.values()) + sum(results2.values())) / 2
    

def prepare_to_plot(values, title, outfile):
    y_pos = [i for i in range(len(values))]
    sorted_keywords, counts = [], []
    for city in sorted(values, key=values.get, reverse=True):
        sorted_keywords.append(city)
        counts.append(values[city])

    pretty_barplot(y_pos, counts, sorted_keywords, 'Diff percentage (%)', title, outfile)

def rank_city_by_uniqueness(sub, outfold, vocabfold='vocabs', thres1=2,thres2=2, at_least_ratio=2, results=0):
    '''
    results:
    - 1: get the difference from the first city only
    - 2: get the difference from the second city only
    - 0: get the average difference
    '''
    print(sub.upper())
    os.makedirs(outfold, exist_ok=True)
    TITLE_TMPL = 'UNIQUENESS COMPARED TO {} BY {}'
    vocabs, totals = {}, {}
    others = Counter()
    for city in ['other'] + config.CITIES:
        vocabs[city] = utils.load_vocab(vocabfold + '/{}/{}.vocab'.format(sub, city), 1)
        totals[city] = sum(vocabs[city].values())
        others += Counter(vocabs[city])

    values = {}
    for city in config.CITIES:
        values[city] = get_diff_vocabs(vocabs[city], vocabs['other'], city, 'Other', thres1, thres2, at_least_ratio, results)

    prepare_to_plot(values, TITLE_TMPL.format('THE REST OF THE WORLD', sub.upper()), os.path.join(outfold, sub + '_world'))
    print('.' * 100)
    values = {}
    for city in config.CITIES:
        values[city] = get_diff_vocabs(vocabs[city], others, city, 'Other cities', thres1, thres2, at_least_ratio, results)
    prepare_to_plot(values, TITLE_TMPL.format('OTHER CITIES', sub.upper()), os.path.join(outfold, sub + '_cities'))
    print('=' * 100)

def get_distribution_other(locfile):
    stopwords = utils.get_stopwords()
    freqs = {}
    with open(locfile, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            freqs[parts[0]] = int(parts[1])

    freqs = utils.filter_stopwords(freqs, stopwords, filter_unprintable=True)

    cloud = wordcloud.WordCloud(background_color="white").generate_from_frequencies(freqs)
    
    fig = plt.figure(figsize=(10, 5))
    plt.imshow(cloud, interpolation='bilinear')
    plt.axis("off")
    plt.title('Locations of Other', fontsize=15)
    plt.show()
    plt.clf()
    plt.close()

# get_distribution_other('loc.vocab')
# rank_city_by_uniqueness('tweets', 'images/unique', thres1=5,thres2=5, at_least_ratio=2, results=2)
# rank_city_by_uniqueness('bios', 'images/unique', thres1=2,thres2=2, at_least_ratio=2, results=2)
# get_popuplarity_distribution('images/pop')