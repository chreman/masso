## Description

Exploration of mentions of "Open Science" in various types of EU-policy documents.
On the basis of the exploration, the hypotheses will be generated.

## Usage

### Setup dependencies

* works best with [Anaconda](https://www.continuum.io/downloads) for Python 3.5:
* First install of Python virtual environment: `conda env create -f masso.yml`
* Activate virtualenv: `source activate masso`
* Install natural language processing models `python -m spacy.en.download all`

### Default pipeline

Run a standardized pipeline that collects documents, extracts content and does preliminary preprocessing
```bash
python3 default_pipeline.py
```


#### Custom crawler usage

```bash
python3 crawl.py --urls pdfs.txt --output pdfs --scrapers scraperdefinitions.json
python3 crawl.py --urls news.txt --output press --scrapers scraperdefinitions.json --xml
python3 crawl.py --urls calls.txt --output calls --scrapers scraperdefinitions.json --html
```

#### Custom scraper usage

```bash
python3 extract.py --input pdfs --convert pdf --output corpus
python3 extract.py --input press --convert xml --stylesheets_path stylesheets.json --classification press --output corpus
python3 extract.py --input calls --convert html --stylesheets_path stylesheets.json --classification calls --output corpus
```

## Analyse and explore with jupyter notebook

* Start the interactive notebook from shell with `jupyter notebook` - assumes crawling and preprocessing has been done

## Requirements

* distinguish between
  * strategy and vision documents
  * work programmes
  * actual calls
* high coverage
* profile immediate and overall contexts of "Open Science"
  * create a conceptual network
* create document network and provenance of documents
* possibly use OKM


## Outcomes and work plan

* collect documents: XML > HTML > PDF
  * specify: corpus management
  * write minimal crawler: give list of links, compare with cache (did I visit this link?), fetch remaining
  * dump HTML, XML, PDF
* extract metadata & fulltexts
  * specify: what metadata, what fulltexts?
  * xml2json
  * scraperdefinitions for different document sources
  * pdf2text
* analysis
  * extract links, EU-IDs, document titles and create document network
    * identify open, outgoing links (-> feed into crawler)
  * co-occurrence on sentence/paragraph/document level
  * apply micro (word2vec) and macro (e.g. topic models) text analysis

1) 8-10h for scrapers und crawler
  * 7.5

2) 6-8h for textextraction
  * 5

3) 12-15h for text mining and analysis
  * 6

4) 10-12h for building a document network
  * 4.5

5) 8-10h for workflow specification and documentation
  * 2

25/40

## ToDO

* look at additional metadata to add to stylesheets
* make topic models/w2v for classification-collections (one for press, one for policy, one for calls)
  * how compare?


## Problems to discuss

* deduplication?
* unique ID of documents?
* PDFs need to manually sorted into folders (e.g. `pdfs-calls, pdfs-press`), so that extractor workflow can assign them appropriate classification
