from crawl import *
from extract import *
from analyse import *
import pathlib
import os



def main(args):
    if args.cleanup:
        with open('visited_links.txt', 'w') as outfile:
            outfile.write("")
        with open('corpus/corpus.json', 'w') as outfile:
            outfile.write("")

    ### crawling section

    scrapers = 'scraperdefinitions.json'

    crawler = Crawler('pdfs.txt', 'pdfs', scrapers, False, False, False)
    crawler.get_urls()

    print("Finished crawling pdfs.")

    crawler = Crawler('press.txt', 'press', scrapers, True, False, False)
    crawler.get_urls()

    print("Finished crawling press releases.")

    crawler = Crawler('calls.txt', 'calls', scrapers, False, False, True)
    crawler.get_urls()

    print("Finished crawling calls.")

    ### extraction section

    output = 'corpus'
    stylesheets_path = 'stylesheets.json'

    extractor = Extractor('pdfs', output, 'pdf', stylesheets_path, 'pdf')
    extractor.convert_files()

    print("Finished extracting from pdfs.")

    extractor = Extractor('press', output, 'xml', stylesheets_path, 'press')
    extractor.convert_files()

    print("Finished extracting from press releases.")

    extractor = Extractor('calls', output, 'html', stylesheets_path, 'calls')
    extractor.convert_files()

    print("Finished extracting from calls.")

    ### analysis section

    inputfolder = 'corpus/corpus.json'
    output = 'results'
    cached_df = None

    if not os.path.exists(output):
        os.makedirs(output)
    corpus = MassoCorpus(inputfolder, output, cached_df)
    if not cached_df:
        corpus.preprocess()
    print("Creating graph.")
    B, labels = corpus.create_graph()
    plot_component_subgraphs(B)
    print("Network graphs exported.")
    nx.write_graphml(B, os.path.join(output, "%s.graphml" %args.name))
    corpus.cache_df(args.name)
    print("DataFrame exported.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download documents in urls.txt from European institutions.')
    parser.add_argument('--output', dest='output', help='relative or absolute path of the output files')
    parser.add_argument('--name', dest='name', help='name of the analysis')
    parser.add_argument('--cleanup', dest='cleanup', help='flag to start with tabula rasa', action='store_true')
    args = parser.parse_args()
    main(args)
