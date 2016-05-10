#!/usr/bin/env python3

"""Short Python module to search for a page in the Python documentation.
"""

import re
import requests
try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


@lru_cache(maxsize=16)
def fetch_index(version='3.5'):
    """Download and parses a genindex-all.html to relevant map of
    keyword -> URL.

    Idea is to get the shortest (generaly shortest is more releavant,
    typically:
    'wait':
       'library/asyncio-subprocess.html#asyncio.asyncio.subprocess.Process.wait'
    vs
    'wait': 'library/os.html#os.wait'

    We're scanning only for HTML anchors, which are relevant keywords
    AND easily linkable, and for each anchors found, we're registering
    the full anchor and its last parts, splitted by dot and dash, so
    that 'term-lambda' is also known under the 'lambda' key, or
    'urllib.request.FTPHandler' is also known as 'FTPHandler'.

    """
    doc_url = 'https://docs.python.org/{}/'.format(version)
    genindex_text = requests.get(doc_url + 'genindex-all.html').text
    index = {}
    links = re.findall('href="(.+?#.+?)"', genindex_text)

    def propose_link(keyword, doc_link):
        """Always get the shortest doc_link.
        """
        if keyword not in index or len(doc_link) < len(index[keyword]):
            index[keyword] = doc_link

    for link in links:
        url, anchor = link.split('#')
        propose_link(anchor, link)
        propose_link(anchor.split('.')[-1], link)
        propose_link(anchor.split('.')[-1].split('-')[-1], link)
        page_name_match = re.search(r'(\w+)\.html', url)
        if page_name_match is not None:
            propose_link(page_name_match.group(1), url)
    return dict([(key, doc_url + value) for key, value in index.items()])


def search(keyword, version='3.5'):
    """
    Search for a keyword in Python documentation.

    >>> search('lambda')
    'https://docs.python.org/3.5/glossary.html#term-lambda'
    >>> search('exit')
    'https://docs.python.org/3.5/library/sys.html#sys.exit'
    """
    return fetch_index(version).get(keyword)


def main():
    def version(argument):
        if re.match('^[0-9.]+$', argument) is None:
            raise ValueError("Argument does not look like a version.")
        return argument

    import argparse
    parser = argparse.ArgumentParser(description='Find a docs.python.org URL.')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--version', default='3.5', type=version)
    parser.add_argument('keyword', nargs='?')
    args = parser.parse_args()
    if args.test:
        import doctest
        doctest.testmod()
    else:
        if args.keyword is None:
            parser.print_help()
            exit(1)
        print(search(args.keyword, args.version))

if __name__ == '__main__':
    main()
