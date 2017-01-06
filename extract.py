#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Download documents from European institutions

Usage:

python3 scrape.py --urls urls.txt --output docs
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
import json
import csv

from lxml import html, etree
import textract

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, filename='extract.log', level=logging.INFO)
logger = logging.getLogger('extractlogger')


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

class Extractor(object):
    """Extract fulltext and metadata from different formats.

    Args:
        input (str): relative or absolute path to the input folder
        output (str): relative or absolute path to the output folder
        convert (str): type of the conversion, one of ["xml", "html", "pdf"]
        stylesheets_path (str): relative or absolute path of the stylesheets definitions
        classification (str): classification of the documents, one of ["press", "call", "pdf"]
    """
    def __init__(self, input, output, convert, stylesheets_path, classification):
        super(Extractor, self).__init__()
        self.input = input
        self.output = output
        self.convert = convert
        self.raws = os.listdir(self.input)
        self.classification = classification
        self.log = logger
        setup_folders(output)
        if stylesheets_path:
            self.stylesheets_path = stylesheets_path
            self.stylesheets = self.load_stylesheets()

    def load_stylesheets(self):
        """Load and return a dictionary of stylesheets."""
        with open(self.stylesheets_path, "r") as infile:
            stylesheets = json.load(infile)
        return stylesheets

    def dump_to_corpus(self, results):
        with open(os.path.join(self.output, "corpus.json"), "a") as outfile:
            outfile.write(json.dumps(results)+"\n")

    def extractFromXML(self, tree):
        """Extract fulltext and metadata from an XML file.

        :param tree: a parsed XML file
        :param type: lxml.ElementTree
        :returns: dictionary
        """
        converter = self.stylesheets.get(self.classification).get('xml')
        results = {}
        for element, value in converter.items():
            try:
                elems = tree.findall(value.get("selector"))
            except Exception:
                continue
            if value.get("attribute") == "text":
                text = [elem.text for elem in elems]
                results[element] = text
            elif value.get("attribute") == "int":
                try:
                    results[element] = [int(elems[0].text)]
                except Exception:
                    self.log.error("Missing value for %s" %element)
            else:
                results[element] = [elem.attrib.get(value.get("attribute")) for elem in elems]

        results["classification"] = self.classification
        if len(results.get("fulltext")) == 0:
            self.log.error("No fulltext found in %d" %results.get("identifier")[0])
        return results

    def extractFromHTML(self, tree):
        """Extract fulltext and metadata from an HTML file.

        :param tree: a parsed HTML file
        :param type: lxml.ElementTree
        :returns: dictionary
        """
        converter = self.stylesheets.get(self.classification).get('html')
        results = {}
        for element, value in converter.items():
            try:
                elems = tree.xpath(value.get("selector"))
            except Exception:
                self.log.error("Could not extract element %s, selector %s" %(element, value.get("selector")))
                continue
            if value.get("attribute") == "text":
                text = [" ".join(list(elem.itertext())) for elem in elems]
                results[element] = text
            elif value.get("attribute") == "href":
                for elem in elems:
                    if elem.text:
                        with open("url_map.csv", "a") as outfile:
                            csvwriter = csv.writer(outfile, delimiter=";", quotechar='"')
                            csvwriter.writerow([elem.attrib.get("href"), elem.text])
                results[element] = [elem.attrib.get(value.get("attribute")) for elem in elems]
            else:
                results[element] = [elem.attrib.get(value.get("attribute")) for elem in elems]
        results["classification"] = self.classification
        return results

    def extractFromPDF(self, pdffile):
        """Extract fulltext and metadata from a PDF file.

        This function applies textract.process(), building on pdfminer,
        to extract the text content from a PDF.

        :param tree: path to a PDF file
        :param type: str
        :returns: dictionary
        """
        results = {}
        _ , tail = os.path.split(pdffile)
        docname, _ = os.path.splitext(tail)
        try:
            results["fulltext"] = textract.process(pdffile, method='pdfminer', encoding='utf-8').decode('utf-8')
        except Exception:
            self.log.error("Could not process %s" %docname)
            return
        results["title"] = docname
        results["local_source"] = pdffile
        results["classification"] = self.classification
        return results

    def convert_files(self):
        if self.convert == "pdf":
            self.pdf2json()

        if self.convert == "xml":
            self.xml2json()

        if self.convert == "html":
            self.html2json()

    def pdf2json(self):
        for raw in self.raws:
            results = self.extractFromPDF(os.path.join(self.input, raw))
            try:
                with open(os.path.join(self.output, results.get("title")+".json"), "w") as outfile:
                    json.dump(results, outfile)
                self.dump_to_corpus(results)
            except Exception:
                self.log.error("Could not process %s" %raw)

    def xml2json(self):
        for raw in self.raws:
            tree = etree.parse(os.path.join(self.input, raw))
            results = self.extractFromXML(tree)
            results["local_source"] = raw
            with open(os.path.join(self.output, str(results.get("identifier")[0])+".json"), "w") as outfile:
                json.dump(results, outfile)
            self.dump_to_corpus(results)

    def html2json(self):
        for raw in self.raws:
            with open(os.path.join(self.input,raw), "r") as infile:
                contents = infile.read()
            tree = html.fromstring(contents)
            results = self.extractFromHTML(tree)
            results["local_source"] = raw
            try:
                with open(os.path.join(self.output, str(results.get("title", results.get('identifier'))[0])+".json"), "w") as outfile:
                    json.dump(results, outfile)
                self.dump_to_corpus(results)
            except Exception:
                self.log.error("Could not dump %s" %results.get('title'))

def main(args):
    extractor = Extractor(args.input, args.output, args.convert, args.stylesheets_path, args.classification)
    extractor.convert_files()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download documents in urls.txt from European institutions.')
    parser.add_argument('--input', dest='input', help='relative or absolute path of the files to convert')
    parser.add_argument('--output', dest='output', help='relative or absolute path of the output files')
    parser.add_argument('--convert', dest='convert', help='type of the conversion, one of ["xml", "html", "pdf"]')
    parser.add_argument('--stylesheets_path', dest='stylesheets_path', help='relative or absolute path of the stylesheets definitions')
    parser.add_argument('--classification', dest='classification', help='classification of the documents, one of ["press", "call"]')
    args = parser.parse_args()
    main(args)
