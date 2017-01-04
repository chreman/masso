import os
import json
import csv
from itertools import chain
import argparse

import pandas as pd
import spacy
import gensim
import networkx as nx
import matplotlib.pyplot as plt

def extract_links(fulltext):
    if fulltext is not pd.np.nan:
        doc = nlp_en(" ".join(fulltext))
        return [str(token) for token in doc if token.like_url]

def extract_entities(fulltext):
    if fulltext is not pd.np.nan:
        doc = nlp_en(" ".join(fulltext))
        return [str(ent) for ent in list(doc.ents)]

def find_entities(fulltext, entities):
    mentions = []
    fulltext = " ".join(fulltext)
    fulltext = " ".join(fulltext.split()).lower()
    for entity in entities:
        if entity in fulltext:
            mentions.append(entity)
    return mentions

def clean_link(link, url2title):
    name = url2title.get(link)
    if name is None:
        head, tail = os.path.split(str(link))
        name, ext = os.path.splitext(tail)
    return name

def plotGraph(G, figsize=(8, 8), filename=None):
    """
    Plots an individual graph, node size by degree centrality,
    edge size by edge weight.
    """
    labels = {n:n for n in G.nodes()}

    try:
        # for networks with only one node
        d = nx.degree_centrality(G)
        nodesize = [v * 250 for v in d.values()]
    except:
        nodesize = [1 * 250 for n in G.nodes()]

    layout=nx.layout.fruchterman_reingold_layout
    pos=layout(G)

    plt.figure(figsize=figsize)
    plt.subplots_adjust(left=0,right=1,bottom=0,top=0.95,wspace=0.01,hspace=0.01)

    # nodes
    nx.draw_networkx_nodes(G,pos,
                            nodelist=G.nodes(),
                            node_color="steelblue",
                            node_size=nodesize,
                            alpha=0.8)
    try:
        weights = [G[u][v]['weight'] for u,v in G.edges()]
    except:
        weights = [1 for u,v in G.edges()]
    nx.draw_networkx_edges(G,pos,
                           with_labels=False,
                           edge_color="grey",
                           width=weights
                        )

    if G.order() < 1000:
        nx.draw_networkx_labels(G,pos, labels, font_size=8)
    if filename:
        plt.savefig(filename)
    plt.close("all")


nlp_en = spacy.load('en')


class MassoCorpus(object):
    """docstring for MassoCorpus"""
    def __init__(self, input, output, cached_df=None):
        super(MassoCorpus, self).__init__()
        if cached_df:
            self.df = self.load_cached_df(cached_df)
        else:
            self.df = pd.read_json(input, lines=True)
        self.output = output
        self.url2title = self.get_url2title()
        self.title2url = self.get_title2url()

    def preprocess(self):
        self.listify_colum('fulltext')
        self.listify_colum('links')
        self.unlistify_colum('title')
        self.df['links2'] = self.df['fulltext'].map(extract_links)
        self.df['entities'] = self.df['fulltext'].map(extract_entities)
        titles = [t.lower() for t in self.df['title'].tolist()]
        self.df['title_mentions'] = self.df['fulltext'].map(lambda x: find_entities(x, titles))
        identifiers = [str(j) for j in list(chain.from_iterable([i for i in self.df['identifier'].tolist() if i is not pd.np.nan]))]
        self.df['identifier_mentions'] = self.df['fulltext'].map(lambda x: find_entities(x, identifiers))
        self.df['links'] = self.df[['links', 'links2']].apply(lambda x: list(chain.from_iterable(x)), axis=1)
        self.remove_nan('links')
        self.df['links'] = self.df['links'].map(lambda x: [l for l in x if "@" not in l]) # filter out email addresses
        self.df['cites'] = self.df['links'].map(lambda x: [clean_link(l, self.url2title) for l in x])
        self.df['targets'] = self.df[['cites', 'title_mentions']].apply(lambda x: list(chain.from_iterable(x)), axis=1)
        self.df['target_links'] = self.df['targets'].map(lambda x: [title2url.get(t) for t in x if title2url.get(t)])

    def cache_df(self, filename):
        self.df.to_pickle(os.path.join(self.output, "%s.pkl" %filename))

    def load_cached_df(self, cached_df):
        return pd.read_pickle(cached_df)

    def get_url2title(self):
        with open("url_map.csv", "r") as infile:
            csvreader = csv.reader(infile, delimiter=";", quotechar='"')
            url2title = {row[0]:row[1].lower() for row in csvreader}
        return url2title

    def get_title2url(self):
        with open("url_map.csv", "r") as infile:
            csvreader = csv.reader(infile, delimiter=";", quotechar='"')
            title2url = {row[1].lower():row[0] for row in csvreader}
        return title2url

    def listify_colum(self, column):
        selection = self.df[self.df[column].map(lambda x: type(x) == list) == False].index
        self.df.ix[selection, column] = self.df.ix[selection][column].map(lambda x: [x])

    def unlistify_colum(self, column):
        selection = self.df[self.df[column].map(lambda x: type(x) == list) == True].index
        self.df.ix[selection, column] = self.df.ix[selection][column].map(lambda x: " ".join(x))

    def remove_nan(self, column):
        self.df[column] = self.df[column].map(lambda x: [i for i in x if i is not pd.np.nan])

    def get_links(self):
        links = self.df['links'].tolist()
        links = [l for l in links if (l is not pd.np.nan and l is not None)]
        links = list(set(chain.from_iterable(links)))
        links = [l for l in links]
        pdfs = [l for l in links if l.endswith('.pdf')]
        htmls = [l for l in links if l.endswith('.html')]
        return (pdfs, htmls)

    def get_fulltexts(self):
        fulltexts = self.df[self.df['fulltext'].notnull()]['fulltext'].tolist()
        return [" ".join(f) for f in fulltexts]

    def get_additional_urls(self):
        pdfs, htmls = self.get_links()
        with open("additional_htmls.txt", "w") as outfile:
            for html in htmls:
                outfile.write(html+"\n")
        with open("additional_pdfs.txt", "w") as outfile:
            for pdf in pdfs:
                outfile.write(pdf+"\n")

    def create_graph(self):
        B = nx.Graph()
        labels = {}
        for row in self.df.iterrows():
            title = (row[1].title)
            targets = (row[1].targets)
            source = title
            targets = [t for t in targets if len(t) > 1]
            if not source in B.nodes():
                B.add_node(source, bipartite=0)
                labels[source] = source
            for target in targets:
                if not target in B.nodes():
                    B.add_node(target, bipartite=1)
                B.add_edge(source, target)
        return B, labels

def main(args):
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    corpus = MassoCorpus(args.input, args.output, args.cached_df)
    if not args.cached_df:
        corpus.preprocess()
    B, labels = corpus.create_graph()
    subgraphs = list(nx.components.connected_component_subgraphs(B, False))
    subgraphs = sorted(subgraphs, key = len, reverse=True)
    for i, sg in enumerate(subgraphs[:1]):
        plotGraph(sg, (24, 24), os.path.join(args.output, str(i)+".svg"))
    for i, sg in enumerate(subgraphs[1:10]):
        plotGraph(sg, (8, 8), os.path.join(args.output, str(i+1)+".svg"))
    nx.write_graphml(B, os.path.join(args.output, "test.graphml"))
    corpus.cache_df("test")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess extracted documents and setup models.')
    parser.add_argument('--input', dest='input', help='relative or absolute path of the corpus.json')
    parser.add_argument('--output', dest='output', help='relative or absolute path of the results folder')
    parser.add_argument('--cached_df', dest='cached_df', help='relative or absolute path of the cached_df')
    args = parser.parse_args()
    main(args)
