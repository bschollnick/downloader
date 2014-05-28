#  -*- coding: utf-8 -*-
"""
Downloader Plugin for acparadise.com.
"""
from bs4 import BeautifulSoup
#http://stackoverflow.com/questions/
#           15997865/beautifulsoup-cant-extract-src-attribute-from-img-tag
import common
import os
import requests
from yapsy.IPlugin import IPlugin

website_base = "http://www.acparadise.com/"
website_cosplayer_index = website_base + \
                        "/acp/display.php?a=%s&t=costumes&page=%s"
                        
website_base_url = "http://www.acparadise.com/acp/display.php?c=%s"
website_photo_base = "http://cosplayers.acparadise.com"

plugin_name = "acparadise"

#
#   test - http://www.acparadise.com/acp/display.php?a=84842
#   http://www.acparadise.com/acp/display.php?c=65016
#   http://www.acparadise.com/acp/display.php?c=63356
#   http://www.acparadise.com/acp/display.php?c=47851
#   http://www.acparadise.com/acp/display.php?c=59294
#   
#   http://www.acparadise.com/acp/display.php?a=89665&t=costumes    # 1 costume
#   http://www.acparadise.com/acp/display.php?a=89607
#   http://www.acparadise.com/acp/display.php?a=89576
#   http://www.acparadise.com/acp/display.php?a=11917&t=costumes&page=6
#   
#
#
#   "Folder" for each cosplay, scrape from website_cosplayer_index
#
# <div class="thumbdescription">
# <a href="display.php?c=76344">Oerba Dia Vanille from Final Fantasy XIII</a>
# </div>
#
#   Costume selection page can have multiples.  check for:
#
#       <div class="normal pagination" align="center">
#       <span class="disabled">&lt;&lt; Previous</span>
#       <span class="current">1</span>
#       <a href="display.php?a=19881&amp;t=costumes&amp;s=&amp;page=2">2</a>
#       <a href="display.php?a=19881&amp;t=costumes&amp;s=&amp;page=2">
#           Next &gt;&gt;</a>
#       </div>
#       Example: http://www.acparadise.com/acp/display.php?a=19881&t=costumes
#
#   Open the page from the hyperlink above, scan for class=thumbtop.
#   Take the img src and remove the -t.  Download that file.
#   continue until out of thumbtop's.
#
#   Uncertain about multiple pages, haven't found one yet.
                                    
class PluginOne(IPlugin):
    """
    Actual Plugin for the Downloader package.
    
    This contains all the customizable content for the cfakes website.
    """
    def __init__(self):
        self.session = requests.session()
        
    def parser_options(self, parser):
        """
            Add the parser options for this plugin
        """
        parser.add_option("--ac",
                          action="store_true", 
                          dest="acparadise",
                          default=False,
                          help="Download from AC Paradise")
        return parser
    
    def print_name(self):
        """
            Example function from yapsy-example.  
        """
        print plugin_name

    def download_acp_cosplayer_index(self, url, timeout):
        """
            Return the cosplay links on the cosplayers index page.
            
            
        """
        current_webpage = common.fetch_webpage(\
                            session=self.session,
                            url=url,
                            timeout=timeout)
        soup = BeautifulSoup(current_webpage)
        links = soup.find_all("div", {"class": "thumbdescription"}) 
        return links


    def extract_ci_details(self, hyperlink):
        """
        Extract the Comic Index Details
        """
        text = str(hyperlink).strip()
        start_dnumber = text.find("?c")+3
        display_page_number = text[start_dnumber:text.find('">',
                                                           start_dnumber)]
        crop_left = text.find('">', start_dnumber)+2
        crop_right = text.find('</a></div>', start_dnumber)
        costume_name = text[crop_left:crop_right].strip().replace(os.sep, "-")
        costume_name = common.clean_filename(costume_name, 
                                             max_length=0)+\
                                             " - %s"%display_page_number
        return (costume_name, display_page_number)
        
    #
    #   Download Gallery
    #
    def download(self, options):
        """
        #   As of 4/24/2014
        #
        #   Examples of 
        #
        """
        print "AC Paradise"
        if options.startingplace != 0:
            counter = options.startingplace
        else:
            counter = 1
        status = common.status()
        while True:
            cosplay_index_links = self.download_acp_cosplayer_index(\
                url=website_cosplayer_index % (options.url_to_fetch,
                                               counter),
                timeout=45)
            if len(cosplay_index_links) == 0:
                #
                #   No download links, stop processing, and return totals
                #
#                return (total_downloaded, total_skipped)
                return status.return_counts()
            else:
                for x in cosplay_index_links:
                    (costume_name, display_page_number) =\
                        self.extract_ci_details(x)
                    costume_name = common.clean_filename(costume_name)

                    print "\nCostume name : %s - %s" % (costume_name, 
                                                        website_base_url%\
                                                        display_page_number)
                    costume_webpage = common.fetch_webpage(\
                                session=self.session,
                                url=website_base_url % display_page_number,
                                timeout=45)
                    costume_soup = BeautifulSoup(costume_webpage)
                    costume_links = costume_soup.find_all("img")    
                    for y in costume_links:
                        if str(y).find(website_photo_base) != -1:
                            #
                            #   Remove thumbnail 
                            #
                            file_to_download = y["src"].replace("-t", "").strip()
                            file_to_download = common.clean_filename(\
                                                file_to_download,
                                                max_length=240)
                                
                                #
                                #   Does directory exist?  If not create it
                                #
                            if not os.path.exists(\
                                        options.download_folder +
                                        costume_name):
                                os.makedirs(options.download_folder + \
                                            costume_name + os.sep)
                                                
                                #   
                                #       Check for file already existing,
                                #        if so, don't download
                                #   
                            if os.path.exists(\
                                        options.download_folder + 
                                        costume_name + os.sep +
                                        os.path.split(file_to_download)[1]):
                                status.add_skipped(filename=file_to_download,
                                                   options=options)
                            else:                                       
                                #
                                #   Download file
                                #
                                if common.download_file(\
                                	    session=self.session,
                                        url=file_to_download,
                                        fileName=os.path.split(file_to_download)[1],
                                        download_folder=options.download_folder +
                                        costume_name + os.sep, timeout=45):
                                    status.add_download(filename=file_to_download,
                                                        options=options)
                                else:
                                    status.add_error(filename=file_to_download,
                                                     options=options)
                
            counter += 1

            #
            #   Increment page count
            #
        return status.return_counts()

    def plugin_run(self):
        """
            meta function for plugin
        """
        common.setup_requests(self.session, website_base)   
            
