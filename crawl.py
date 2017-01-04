#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Download documents from European institutions

"""


__author__ = "Christopher Kittel"
__copyright__ = "Copyright 2016"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Christopher Kittel"
__email__ = "web@christopherkittel.eu"
__status__ = "Prototype" # 'Development', 'Production' or 'Prototype'


import requests
import urllib

import os
import sys
import argparse
import logging
import time

from lxml import html
import json
import csv

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, filename='crawl.log', level=logging.INFO)
logger = logging.getLogger('crawllogger')

def drawProgressBar(percent, barLen = 20):
    """
    Draw a progress bar to the command line.
    """
    sys.stdout.write("\r")
    progress = ""
    for i in range(barLen):
        if i < int(barLen * percent):
            progress += "="
        else:
            progress += " "
    sys.stdout.write("[ %s ] %.2f%%" % (progress, percent * 100))
    sys.stdout.flush()

def print_progress(m, n, url):
    sys.stdout.write("\r")
    sys.stdout.write("(%d / %d) Now downloading %s" %(m,n,url))

def setup_folders(foldername):
    """
    Check whether outfolder folder and path exist, create them if necessary.
    """
    if not os.path.exists(foldername):
        os.makedirs(foldername)

class Crawler(object):
    """docstring for Crawler"""
    def __init__(self, urls, output, scrapers, xml, pdf, html):
        super(Crawler, self).__init__()
        self.urls = urls
        self.output = output
        self.scrapers = scrapers
        self.xml = xml
        self.pdf = pdf
        self.html = html
        self.url_mapper = self.get_url_mapper()
        self.log = logger
        setup_folders(output)

    def get_url_mapper(self):
        with open("url_map.csv", "r") as infile:
            csvreader = csv.reader(infile, delimiter=";", quotechar='"')
            url_mapper = {row[0]:row[1] for row in csvreader}
        return url_mapper

    def get_cached(self):
        with open("visited_links.txt", "r") as infile:
            visited = [l.strip() for l in infile.readlines()]
        return set(visited)

    def get_urls(self):
        with open(self.urls, "r") as infile:
            urls = list(row.strip() for row in infile.readlines())
        with open(self.scrapers, "r") as infile:
            scrapers = json.load(infile)
        urls = [url for url in urls if not url in self.get_cached()]
        self.log.info("%d new urls to crawl." %len(urls))
        m = 1
        n = len(urls)
        for url in urls:
            time.sleep(2)
            print_progress(m,n,url)
            if url.endswith('.pdf'):
                self.get_PDF_directly(url)
                self.log.info("Directly getting PDF, %s" %url)
                m += 1
                continue

            netloc = urllib.parse.urlparse(url).netloc
            if netloc is None:
                self.log.error("No netloc for malformed url %s" %url)
                continue

            scraper = scrapers.get(netloc)
            if scraper is None:
                self.log.error("No scraper for %s, cannot crawl %s" %(netloc, url))
                continue

            self.get_url(url, scraper)
            with open("visited_links.txt", "a") as outfile:
                outfile.write(url+"\n")
            m += 1

    def get_content(self, url, tree, scraper, content_type):
        href = tree.xpath(scraper.get(content_type).get("selector"))[0]
        try:
            to_download = urllib.parse.urljoin(url, href)
            response = urllib.request.urlopen(to_download)
        except Exception:
            self.log.exception("Could not download %s" %to_download)
        head, tail = os.path.split(to_download)
        with open(os.path.join(self.output, tail), "wb") as outfile:
            outfile.write(response.read())
        with open("download_log.csv", "a") as outfile:
            csvwriter = csv.writer(outfile, delimiter=";", quotechar='"')
            csvwriter.writerow([tail, url])

    def clean_link(self, link):
        title = self.url_mapper.get(link)
        head, tail = os.path.split(link)
        name, ext = os.path.splitext(tail)
        return title, name

    def get_PDF_directly(self, url):
        try:
            s = urllib.request.urlopen(url)
            contents = s.read()
        except Exception:
            self.log.error("Could not read: %s" %url)
            return
        title, name = self.clean_link(url)
        try:
            with open(os.path.join(self.output, title)+".pdf", "wb") as outfile:
                outfile.write(contents)
        except:
            with open(os.path.join(self.output, name)+".pdf", "wb") as outfile:
                outfile.write(contents)
        with open("visited_links.txt", "a") as outfile:
            outfile.write(url+"\n")

    def get_url(self, url, scraper):
        try:
            s = urllib.request.urlopen(url)
            contents = s.read()
        except Exception:
            self.log.error("Could not read: %s") %url
            return
        tree = html.fromstring(contents)
        netloc = urllib.parse.urlparse(url).netloc
        results = {}

        if self.html:
            with open(os.path.join(self.output, url.replace("/", "_")), "wb") as outfile:
                outfile.write(contents)
            with open("download_log.csv", "a") as outfile:
                csvwriter = csv.writer(outfile, delimiter=";", quotechar='"')
                csvwriter.writerow([url.replace("/", "_"), url])

        if self.xml:
            self.get_content(url, tree, scraper, 'xml')

        if self.pdf:
            self.get_content(url, tree, scraper, 'pdf')

def main(args):
    crawler = Crawler(args.urls, args.output, args.scrapers, args.xml, args.pdf, args.html)
    crawler.get_urls()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download documents in urls.txt from European institutions.')
    parser.add_argument('--urls', dest='urls', help='relative or absolute path of the urls.txt')
    parser.add_argument('--output', dest='output', help='relative or absolute path of the output folder')
    parser.add_argument('--scrapers', dest='scrapers', help='relative or absolute path of the scraper definitions')
    parser.add_argument('--xml', dest='xml', help='flag to download XML', action='store_true')
    parser.add_argument('--pdf', dest='pdf', help='flag to download PDF', action='store_true')
    parser.add_argument('--html', dest='html', help='flag to download HTML', action='store_true')
    args = parser.parse_args()
    main(args)
