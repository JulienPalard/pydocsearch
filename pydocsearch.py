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
def fetch_index(doc_url='https://docs.python.org/3.5/'):
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
    genindex_text = requests.get(doc_url + 'genindex-all.html').text
    index = {}
    links = re.findall('href="(.+?#.+?)"', genindex_text)
    for link in links:
        url, anchor = link.split('#')
        after_last_dot = anchor.split('.')[-1]
        after_last_dash = anchor.split('.')[-1].split('-')[-1]
        for key in (anchor, after_last_dot, after_last_dash):
            index[key] = doc_url + min((index.get(key, link), link), key=len)
    return index


def search(keyword):
    """
    Search for a keyword in Python documentation.

    >>> search('lambda')
    'https://docs.python.org/3.5/glossary.html#term-lambda'
    >>> search('exit')
    'https://docs.python.org/3.5/library/sys.html#sys.exit'
    """
    index = fetch_index()
    return index.get(keyword)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
