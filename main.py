# %%
import os
import requests
import bs4
import urllib
import sys
import argparse
from math import ceil
from tqdm import tqdm
from unicodedata import normalize

# %%
books_per_page = 10
url_categories = 'https://link.springer.com/search/facetexpanded/discipline?facet-content-type=%22Book%22&package=mat-covid19_textbooks'
urlbase = 'https://link.springer.com/'

# %%
def getCategories(url_categories):
    res = requests.get(url_categories)
    content = bs4.BeautifulSoup(res.text, 'html.parser')
    number_of_classes = int(content.select_one('.number-of-pages').text)
    categories = []

    for c in range(1, number_of_classes + 1):
        res = requests.get(f'{url_categories}&page={c}')
        content = bs4.BeautifulSoup(res.text, 'html.parser')
        category_buffer = [x.select_one('a').text.split('\n')[2] for x in content.select_one('ol').select('li')]
        categories.extend(category_buffer)
    return categories

def downloadCategory(category, urlbase, destination, media_types):
    query = 'facet-content-type=' + urllib.parse.quote_plus('\"Book\"') + '&just-selected-from-overlay-value=' + urllib.parse.quote_plus(f'\"{category}\"') + '&just-selected-from-overlay=facet-discipline&package=mat-covid19_textbooks&facet-discipline='+ urllib.parse.quote_plus(f'\"{category}\"')
    url_category = f'https://link.springer.com/search?{query}'
    res = requests.get(url_category)
    content = bs4.BeautifulSoup(res.text, 'html.parser')
    number_of_books = int(content.select_one('#number-of-search-results-and-search-terms').select_one('strong').text)

    if number_of_books > 0:
        print(f'Downloading {number_of_books} book(s) for {category}')
        number_of_pages = ceil(number_of_books / books_per_page)
        book_list=[]

        with tqdm(total=number_of_books) as pbar:
            for n in range(1, number_of_pages + 1):
                url_category = f'https://link.springer.com/search/page/{n}?{query}'
                res = requests.get(url_category)
                content = bs4.BeautifulSoup(res.text, 'html.parser')
                book_list = [x.select_one('a').get_attribute_list('href')[0] for x in content.select_one('.content-item-list').select('h2')]
                for book_url in book_list:
                    downloadBook(urlbase+book_url, category, urlbase, destination, media_types)
                    pbar.update(1)

def downloadBook(book_url, category, urlbase, destination, media_types):
    res = requests.get(book_url)
    content = bs4.BeautifulSoup(res.text,'html.parser')
    title = content.select_one('.page-title').select_one('h1').text.replace('/','_')
    authors = '; '.join([normalize('NFKC', x.text) for x in content.select('.authors__name')]).replace('/', '_')

    for media_type in media_types:
        try:
            download_link = content.select_one(f'a[data-track-action="Book download - {media_type}"]').get_attribute_list('href')[0]
            download_dir_path = os.path.join(destination, category.replace('/','-'))
            download_full_path = os.path.join(download_dir_path, f'({authors}) {title}.{media_type.lower()}')

            if not os.path.exists(download_dir_path):
                os.mkdir(download_dir_path)
            if not os.path.exists(download_full_path):
                r = requests.get(urlbase + download_link)
                with open(download_full_path, 'wb') as f:
                    f.write(r.content)
        except:
            pass

# %%
def parseArgs():
    parser = argparse.ArgumentParser(description='Downloads Springer free ebooks')
    parser.add_argument('destination', action='store',
                        help='Path where the files will be downloaded')
    parser.add_argument('--pdf', dest='media_types', action='append_const', const='pdf',
                        help='Downloads PDF version of the books')
    parser.add_argument('--epub', dest='media_types', action='append_const', const='ePub',
                        help='Downloads EPUB version of the books')

    args = parser.parse_args()

    if args.media_types is None:
        parser.error('--pdf and/or --epub must be set')

    return args

def run(args):
    if not os.path.exists(args.destination):
        os.mkdir(args.destination)

    print(f'Downloading books into {args.destination}')
    categories = getCategories(url_categories)

    for category in categories:
        downloadCategory(category.replace('/','-'), urlbase, args.destination, args.media_types)

    print('Done!!!')

def main():
    args = parseArgs()
    run(args)

if __name__ == '__main__':
    main()