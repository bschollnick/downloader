"""
Downloader Plugin for acparadise.com.
"""
import httplib
import os
import random
import requests
try:
	import requests_cache
	RCACHE = True
except ImportError:
	RCACHE = False

import sys
import unidecode
import urllib2

USERAGENTS = (
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.202 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)',
    'Opera/9.99 (Windows NT 5.1; U; pl) Presto/9.9.9',
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/ Safari/530.5',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/6.0',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)'
    )


def is_int(value_to_test):
    """
    Test to see if string is an integer.

    If integer, returns True.
    If not integer, returns False.

    note, exception tracking tests to be slower!
    """
    if value_to_test.isdigit():
        return True
    else:
        return False

def post_webpage(session, url, data=None, timeout=30, binary=False):
    """
    post the webpage at url.
    This returns the actual page text for scraping.
    """
    if data == None:
        return
    error = False
    try:
        page = session.post(url, data=data, timeout=timeout)
    except urllib2.HTTPError:
        print "Bad URL? - %s" % url
        error = True
    except urllib2.URLError:
        print "Bad URL? - %s" % url
        error = True
    except httplib.BadStatusLine:
        print "Bad HTTP Status Line?"
        error = True
    except httplib.IncompleteRead:
        print "Incomplete Read"
        error = True
    except requests.exceptions.ConnectionError:
        print "Connection Error"
        error = True
    except requests.exceptions.Timeout:
        print "Timeout"
        error = True

    if error:
        return

    if not binary:
        return page.text
    else:
        return page.contents

def fetch_webpage(session,
                  url,
                  timeout=30,
                  binary=False,
                  headers=None):
    """
    Fetch the webpage at url.
    This returns the actual page text for scraping.
    """
    try:
        if not headers:
            headers = {'User-Agent': USERAGENTS[7],
                       'Referer' : url}

#        if cookie != None:
#        	page = session.get(url,
#        	                   timeout=timeout,
#        	                   headers=headers,
#        	                   cookies=cookie)
#        else:
#        print session.cookies
      	page = session.get(url, timeout=timeout, headers=headers)

        if not binary:
            return page.text
        else:
            return page.contents

    except urllib2.HTTPError:
        print "Bad URL? - %s" % url
    except urllib2.URLError:
        print "Bad URL? - %s" % url
    except httplib.BadStatusLine:
        print "Bad HTTP Status Line?"
    except httplib.IncompleteRead:
        print "Incomplete Read"
    except requests.exceptions.ConnectionError:
        print "Connection Error"
    except requests.exceptions.Timeout:
        print "Timeout"
    return


    #
    #
    #
def setup_requests(session, base_url):
    """
    This initializes and performs a test fetch to the website to prime
    requests, and setup the session.
    """
    session = requests.session()
    if RCACHE:
    	requests_cache.install_cache("downloader_cache")
    fetch_webpage(session, url=base_url, timeout=60)
    return session

def clean_filename(filename, max_length=0, unicode_filter=True):
    """
    Sanitize the filename
    """
    filename = urllib2.unquote(filename)

    if unicode_filter:
        filename = unidecode.unidecode(filename)

    filename = filename.replace("'", "`").replace(",", "")
    filename = filename.replace('"', "`").replace("#", "")
    if len(filename) >= max_length >= 1:
        filename = filename[:max_length] + os.path.splitext(filename)[1]
    return filename

def replace_all(text, dic):
    """
    Helper function for Clean Filename2
    """
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

def clean_filename2(filename,
                    max_length=0,
                    replacements={'"':"`", "'":"`", ",":"", "#":"", '/':"-", ":":"-", "?":"", ">":"-", "<":"-"},
                    unicode_filter=True):
    """
    Looking to clean up clean_filename, and make it more generic
    """
    filename = replace_all(urllib2.unquote(filename), replacements)
    if unicode_filter:
        filename = unidecode.unidecode(filename)
    if max_length >= 1:
        filename = filename[:max_length] + os.path.splitext(filename)[1]
    return filename

def download_file(session,
                  url,
                  filename=None,
                  download_folder="",
                  timeout=30,
                  cookies=None):
    """
    Download the file at URL.

    Files will be written to download_folder

    returns downloaded, and already_exists

    rewrite - using info from here?

    http://stackoverflow.com/questions/13137817/
            how-to-download-image-using-requests
    """
    if cookies == None:
        cookies = {}
    headers = {'Referer': url,
               'User-Agent' : random.choice(USERAGENTS)}
    downloaded = False
    error = False
    try:
        results = session.get(url,
                              headers=headers,
                              timeout=timeout,
                              stream=True)
        if results.ok:
            #   http://stackoverflow.com/questions/16694907/
            #   how-to-download-large-file-in-python-with-requests-py
            with open(download_folder + filename, "wb") as outf:
                for chunk in results.iter_content(chunk_size=256):
                    if chunk:
                        outf.write(chunk)
                outf.flush()
            downloaded = True

    except (urllib2.HTTPError, urllib2.URLError):
        print "Bad URL? - %s" % url
        error = True
    except httplib.BadStatusLine:
        print "Bad HTTP Status Line?"
        error = True
    except httplib.IncompleteRead:
        print "Incomplete Read"
        error = True
    except requests.exceptions.ConnectionError:
        print "Connection Error"
        error = True
    except requests.exceptions.Timeout:
        print "Timeout"
        error = True
    except requests.exceptions.ChunkedEncodingError:
        error = True
        print "Bad chunk"
    except IOError:
        error = True
        print "\n Error Writing %s" % filename

    if error:
        return False

    return downloaded

class   status(object):
    """
    Status Counter for downloader
    """
    def __init__(self):
        self.total_downloads = 0
        self.total_errors = 0
        self.total_skipped = 0

    def add_download(self, filename, options):
        """
        Increment the download counter
        """
        self.total_downloads += 1
        if options.silent:
            pass
        else:
            if options.details:
                print "Downloaded: %s" % filename
            else:
                print "D",
                if self.total_downloads % 2 == 1:
                    sys.stdout.flush()
        return

    def return_downloads(self):
        """
        Return the download counter
        """
        return self.total_downloads

    def add_error(self, filename, options):
        """
        Increment the error counter
        """
        self.total_errors += 1
        if options.silent:
            pass
        else:
            if options.details:
                print "Error: %s" % filename
            else:
                print "E",
                if self.total_errors % 2 == 1:
                    sys.stdout.flush()
        return

    def return_errors(self):
        """
        return the download counter
        """
        return self.total_errors

    def add_skipped(self, filename, options):
        """
        Increment the add counter
        """
        self.total_skipped += 1
        if options.silent:
            pass
        else:
            if options.details:
                print "Skipped: %s" % filename
            else:
                print ".",
                if self.total_skipped % 2 == 1:
                    sys.stdout.flush()
        return

    def return_skipped(self):
        """
        return the download counter
        """
        return self.total_skipped

    def return_counts(self):
        """
        return all the counters
        """
        return (self.total_downloads, self.total_skipped, self.total_errors)
