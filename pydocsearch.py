#!/usr/bin/env python3

"""Short Python module to search for a page in the Python documentation.
"""

import re
import math
import requests
try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


class PydocIndexEntry:
    weights = {
        # From number of visitors:
        'functions.html': 1,
        'glossary.html': 1,
        'stdtypes.html': .9,
        'string.html': .8,
        're.html': .7,
        'datetime.html': .6,
        'builtins.html': .5,
        'exceptions.html': .1,
        # Manual bonuses:
        # To get __str__ from datamodel instead of datetime:
        'datamodel.html': .8,
        # To get __add__ from operators instead of datamodel:
        'operator.html': .8
    }

    def __init__(self, keyword):
        self.keyword = keyword
        self.links = {}
        self.best_link = None

    def link_weight(self, doc_link):
        """Compute the weight of a link.
        Observed signals are:
         - Shorter is generally better
         - Highly visited pages are better

        Each criterion is in between 0 and 1 so we can eventually
        weight them.
        """
        page_re = re.search(r'\w+\.html', doc_link)
        page = page_re.group(0) if page_re is not None else ''
        visit_weight = self.weights.get(page, 0)
        length_weight = 1 / math.sqrt(len(doc_link))
        return length_weight + visit_weight

    def register(self, doc_link):
        doc_link_weight = self.link_weight(doc_link)
        self.links[doc_link] = doc_link_weight
        if self.best_link is None:
            self.best_link = doc_link
        elif doc_link_weight > self.links[self.best_link]:
            self.best_link = doc_link


class PydocIndex:
    def __init__(self, doc_url):
        self.doc_url = doc_url
        self.index = {}

    def get_or_create_entry(self, keyword):
        keyword = keyword.lower()
        if keyword not in self.index:
            self.index[keyword] = PydocIndexEntry(keyword)
        return self.index[keyword]

    @classmethod
    @lru_cache(maxsize=16)
    def load_from(cls, version='3.5'):
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
        pydoc_index = cls(doc_url)
        genindex_text = requests.get(doc_url + 'genindex-all.html').text
        links = re.findall('href="(.+?#.+?)">([^<]+)</a>', genindex_text)
        for (link, text) in links:
            url, anchor = link.split('#')
            anchor_chunks = re.split(r'\W', anchor)
            for chunks in ['.'.join(keywords[-i-1:]) for i, keywords in
                           enumerate([anchor_chunks] * len(anchor_chunks))]:
                pydoc_index.get_or_create_entry(chunks).register(link)
            page_name_match = re.search(r'(\w+)\.html', url)
            if page_name_match is not None:
                pydoc_index.get_or_create_entry(page_name_match.group(1)).register(url)
            pydoc_index.get_or_create_entry(text).register(link)
        return pydoc_index

    def search(self, keyword):
        hardcoded = {'pip': 'installing/index.html'}
        if keyword in hardcoded:
            return self.doc_url + hardcoded[keyword]
        try:
            return self.doc_url + self.index[keyword.lower()].best_link
        except KeyError:
            return None


def search(keyword, version='3.5'):
    """
    Search for a keyword in Python documentation.

    >>> search('lambda')
    'https://docs.python.org/3.5/glossary.html#term-lambda'
    >>> search('exit')
    'https://docs.python.org/3.5/library/sys.html#sys.exit'
    """
    return PydocIndex.load_from(version).search(keyword)


def main():
    def version(argument):
        if re.match('^[0-9.]+$', argument) is None:
            raise ValueError("Argument does not look like a version.")
        return argument

    import argparse
    parser = argparse.ArgumentParser(description='Find a docs.python.org URL.')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--dump', action='store_true',
                        help="Dump index (to check consistency)")
    parser.add_argument('--light-dump', action='store_true',
                        help="Light dump index (to diff)")
    parser.add_argument('--version', default='3.5', type=version)
    parser.add_argument('keyword', nargs='?')
    args = parser.parse_args()
    if args.dump:
        pydoc_index = PydocIndex.load_from(args.version)
        for entry in pydoc_index.index.values():
            print(entry.keyword)
            for link, link_weight in entry.links.items():
                print("{} {} {:.2f}".format(
                    ' -> ' if link == entry.best_link else ' -- ',
                    link,
                    link_weight))
        exit(0)
    if args.light_dump:
        pydoc_index = PydocIndex.load_from(args.version)
        for entry in sorted(pydoc_index.index.values(),
                            key=lambda item: item.keyword):
            print(entry.keyword, entry.best_link)
        exit(0)
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
