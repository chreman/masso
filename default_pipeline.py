from crawl import *
from extract import *
import pathlib




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

    crawler = Crawler('news.txt', 'press', scrapers, True, False, False)
    crawler.get_urls()

    crawler = Crawler('calls.txt', 'calls', scrapers, False, False, True)
    crawler.get_urls()

    ### extraction section

    output = 'corpus'
    stylesheets_path = 'stylesheets.json'

    extractor = Extractor('pdfs', output, 'pdf', stylesheets_path, 'pdf')
    extractor.convert_files()

    extractor = Extractor('press', output, 'xml', stylesheets_path, 'press')
    extractor.convert_files()

    extractor = Extractor('calls', output, 'html', stylesheets_path, 'calls')
    extractor.convert_files()

    ### analysis section


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download documents in urls.txt from European institutions.')
    parser.add_argument('--output', dest='output', help='relative or absolute path of the output files')
    parser.add_argument('--cleanup', dest='cleanup', help='flag to start with tabula rasa', action='store_true')
    args = parser.parse_args()
    main(args)
