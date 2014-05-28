"""
Downloader Plugin for acparadise.com.
"""
#   http://stackoverflow.com/questions/15997865/beautifulsoup-cant-extract-src-attribute-from-img-tag
import httplib
import os
import random
import requests
import sys
import unicodedata
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


def post_webpage(session, url, data={}, timeout=30, binary=False):
    """
    post the webpage at url.
    This returns the actual page text for scraping.
    """
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

def fetch_webpage(session, url, timeout=30, binary=False, headers=None):
    """
    Fetch the webpage at url.
    This returns the actual page text for scraping.
    """
    try:
        if not headers:
            headers = {'User-Agent': USERAGENTS[7],
                       'Referer' : url}
        
        page = session.get(url, timeout=timeout, headers=headers)
        if not binary:
            return page.text
        else:
            return page.contents
        
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

    return 
        
 
    #
    #
    #
def setup_requests(session, base_url):
    """
    This initializes and performs a test fetch to the website to prime
    requests, and setup the session.
    """
#    headers = {'User-Agent':    USERAGENTS[7],
#               'Referer'   :   base_url}
#    session.get(base_url, headers=headers)
    session = requests.session()
    fetch_webpage(session, url=base_url, timeout=60)
    return session
    
"""
Sanitize the filename

http://stackoverflow.com/questions/1207457/
    convert-unicode-to-a-string-in-python-containing-extra-symbols

http://stackoverflow.com/questions/436220/
    python-is-there-a-way-to-determine-the-encoding-of-text-file

http://stackoverflow.com/questions/7623476/
    how-can-encodeascii-ignore-through-a-unicodedecodeerror
"""
def clean_filename(filename, max_length=0):
    filename = urllib2.unquote ( filename )
    #filename = filename.decode('ascii', 'ignore').encode('ascii', 'ignore')
    #filename = filename.encode('ascii','xmlcharrefreplace')
    #filename = unicode(filename, "utf-8")
    #filename = unicodedata.normalize('NFKD',unicode(filename)).encode('ascii', 'ignore')
        # http://stackoverflow.com/questions/2365411/
        #           python-convert-unicode-to-ascii-without-errors
        #
        #   Changes Unicode to the &xxx; format in the filename
    import unidecode
    filename = unidecode.unidecode ( filename )

    filename = filename.replace("'", "`").replace(",", "")
    filename = filename.replace('"', "`").replace("#", "")
    if len(filename) >= 250 and max_length >= 1:
        filename = filename[1:max_length] + os.path.splitext(filename)[1]
    return filename
        

def download_file(session,
                  url,
                  fileName=None,
                  download_folder="",
                  timeout=30):
    """
    Download the file at URL.  
    
    Files will be written to download_folder
    
    returns downloaded, and already_exists
    
    rewrite - using info from here?
    
    http://stackoverflow.com/questions/13137817/
            how-to-download-image-using-requests
    """
      
    headers = {'Referer': url,
               'User-Agent' : random.choice(USERAGENTS)}

    downloaded = False
    error = False
    try:
        r = session.get(url, 
                        headers=headers, 
                        timeout=timeout,
                        stream=True)
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
        return False
        
    if not error and r.ok:
        downloaded = True
        try:
            #   http://stackoverflow.com/questions/16694907/
            #   how-to-download-large-file-in-python-with-requests-py
            with open(download_folder + fileName, "wb") as f:
                for chunk in r.iter_content (chunk_size=256):
                    if chunk:
                        f.write(chunk)
                f.flush()
#            local_file = open(download_folder + fileName, "wb")
#           local_file.write(r.content)
#            local_file.close()
        except IOError:
            print "\n Error Writing %s" % fileName
        finally:   
            pass

        return downloaded

class   status:
    def __init__(self):
        self.total_downloads = 0
        self.total_errors = 0
        self.total_skipped = 0
        
    def add_download(self, filename, options):
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
        return self.total_downloads
        
    def add_error(self, filename, options):
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
        return self.total_errors
         
    def add_skipped(self, filename, options):
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
        return self.total_skipped
    
    def return_counts(self):
        return (self.total_downloads, self.total_skipped, self.total_errors)