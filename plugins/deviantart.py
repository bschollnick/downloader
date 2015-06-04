#  -*- coding: utf-8 -*-
"""
Downloader Plugin for cfakes.com.
"""
from bs4 import BeautifulSoup
import common
import os
import requests
import scandir
import sys
import time
from yapsy.IPlugin import IPlugin

WEBSITE_NAME = "http://www.deviantart.com"
#WEBSITE_BASE_URL = "%s/photos/" % WEBSITE_NAME

plugin_name = "deviantart"


class PluginOne(IPlugin):

    """
    Actual Plugin for the Downloader package.

    This contains all the customizable content for the cfakes website.
    """

    def __init__(self):
        self.session = requests.session()
        self.root_checker = {}
        #self.safari_cookies = returnBinaryCookies.main()
       # self.extracted_cookie = {"www.deviantart.com":urllib.unquote(
       # self.safari_cookies["www.hypnopics-collective.net"])}
#        print self.extracted_hp_cookie

    def parser_options(self, parser):
        """
            Add the parser options for this plugin
        """
        parser.add_option("--da2", "--deviantart",
                          action="store_true",
                          dest="deviantart",
                          default=False,
                          help="Download from deviantart.com with Folders",)

        parser.add_option("--user",
                          action="store",
                          dest="username",
                          default="",
                          help="UserName to Login with",)

        parser.add_option("--password",
                          action="store",
                          dest="password",
                          default="",
                          help="Password to Login with",)

        return parser

    def print_name(self):
        """
            Example function from yapsy-example.
        """
        print plugin_name

    #
    #   Verify Login
    #
    def login(self, options):
        """
        Not used, since cfakes does not require a login.
        """
        #   http://stackoverflow.com/questions/17226080
        #           /parsing-html-forms-input-tag-with-beautiful-soup

        print "\nTrying to login to Deviantart\n"
        # This is the form data that the page sends when logging in
        #   <input type="hidden" name="validate_token"
        #       value="2f1810a29dc923636245" autocomplete="off">
        #   <input type="hidden" name="validate_key"
        #       value="1376387679" autocomplete="off">

        soup = BeautifulSoup(common.fetch_webpage(
            session=self.session,
            url="https://www.deviantart.com/users/login",
            timeout=45,
            binary=False))
        data = soup.find_all("input", type="hidden")
        validate_token = None
        validate_key = None

        search_data = soup.find_all('input',
                                    {'type': 'hidden',
                                     'name': 'validate_token'})
        validate_token = search_data[0]["value"]
        search_data = soup.find_all('input',
                                    {'type': 'hidden',
                                     'name': 'validate_key'})
        validate_key = search_data[0]["value"]
        form_data = {
            'username': options.username,
            'password': options.password,
            'remember_me': '1',
            'submit': 'Login',
            'ref': '',
            'validate_token': validate_token,
            'validate_key': validate_key
        }

        data = common.post_webpage(session=self.session,
                                   url='https://www.deviantart.com/users/login',
                                   data=form_data)

        data = common.fetch_webpage(session=self.session,
                                    url='http://www.deviantart.com/')
        if data.find('"loggedIn":true') == -1:
            print "\nUnable to Login!  Aborting. \n"
            print data
            sys.exit(1)
        elif data.find('<span class="field_error" rel="password">') != -1:
            # elif data.find('<span class="field_error" rel="password">The
            # password you entered was incorrect.</span>') != -1:
            print "\nBad DeviantArt Password.  Aborting. \n"
            sys.exit(1)
        else:
            print "\nLogin to DeviantArt successful!\n"

    #
    #   Find Folders in Gallery Page
    #
    def search_for_folders(self, soup_bowl):
        """
        Takes the contents of a BeautifulSoup container, and
        checks for known gallery / folder markers.

        This will return an list of:

            Folder Name, Folder URL

        """
        found_urls = []
        folder_count = 1

        #
        #   div's with Class tv150
        #
        tv150_tags = soup_bowl.find_all('div', {'class': 'tv150'})
        for tgx in tv150_tags:
            folder_name = tgx.find_all("div", {"class": "tv150-tag"})[0].text
            folder_url = tgx.find_all("a", {'class': 'tv150-cover'})[0]["href"]
            found_urls.append((folder_name, folder_url))
            # http://nirufe.deviantart.com/gallery/
            # <a href="http://yayacosplay.deviantart.com/gallery/33798593"
            # class="tv150-cover"></a>

        #
        #   div's with class rs-customicon-cont
        #
        customicons = soup_bowl.find_all(
            'div', {'class': 'rs-customicon-cont'})
        for c_icon in customicons:
            folder_url = c_icon.find_all("a",\
                {"class": "rs-customicon-link"})[0]["href"]
            try:
                folder_name = c_icon.find_all("a", {'class': ''})[0].text
            except IndexError:
                print "\t\tFailure to find description"
                folder_name = "FolderName %s" % folder_count
                folder_count += 1
            found_urls.append((folder_name, folder_url))
            #   <a href="http://ulorinvex.deviantart.com/gallery/977878"
            #               class="rs-customicon-link">
            #<img src="http://a.deviantart.net/gallerythumbs/8/
            #               7/000977878.jpg?3"
            #        alt="">
            #   </a>

        #
        #   div with class of gl-text
        #
        class_a_tags = soup_bowl.find_all('div', {'class': 'gl-text'})
        for at_x in class_a_tags:
            #   Class A tags require a filter, since those custom setups
            #   seem to use the class="a" on all hyperlinks, not just for
            #   the gallery folders.
            #
            #   So check to see if the href has the server name.
            folder_name = at_x.find_all("a", {"class": "a"})[0].text
            folder_url = at_x.find_all("a", {"class": "a"})[0]["href"]
            found_urls.append((folder_name, folder_url))

            #<div style="line-height:1.3em" class="gl-text"
            #       collect_rid="20:32170436">
            #<a class="a"
            #   href="http://arconius.deviantart.com/gallery/32170436">
            #   Ponies</a>
            #</div>
        return found_urls

    def download(self, options):
        """
        Start the download process, meta manager.

        Grab the folder list from DA, and process each folder
        """
        self.session = common.setup_requests(self.session, WEBSITE_NAME)
        if options.username:
            #
            #   Use login information, if provided.
            #
            self.login(options)

        status = common.status()
        status = self.download_gallery(options.url_to_fetch,
                                       options.download_folder,
                                       options,
                                       status,
                                       root=True)

        return status.return_counts()

    def download_gallery(self,
                         gallery_url,
                         download_path,
                         options,
                         status,
                         root=False):
        """
            Download an complete gallery, calls download_gallery_images
            for the actual image download.

            This creates the folder structure, and walks through it
            calling download_gallery_images to download the images.
        """
        current_webpage = common.fetch_webpage(session=self.session,
                                               url=gallery_url,
                                               timeout=45)
        soup = BeautifulSoup(current_webpage)
        #
        #   Grab the main web page from the URL to fetch
        #
        #   Search for folders
        folder_list = self.search_for_folders(soup_bowl=soup)
        for (subgallery_name, subgallery_url) in folder_list:
             #
             #   Process the folder list, and download
             #   the images for the subfolders
             #
            if options.downloadlimit > 0 and \
                    status.return_downloads() >= options.downloadlimit:
                print "X",
                return status
            if subgallery_name != None:
                subgallery_dl_path = download_path + os.sep +\
                    common.clean_filename(subgallery_name) + os.sep
            if subgallery_url != gallery_url:
                #
                #   Clubs typically have the featured gallery which points to
                #   itself and can cause a recursion loop
                #
                status = self.download_gallery(subgallery_url,
                                               subgallery_dl_path,
                                               options,
                                               status,
                                               root=False)
            time.sleep(1)
        gallery_name = soup.title.text
        gallery_name = gallery_name[0:gallery_name.find(" by ")].strip()

        if root:
            for root, dirnames, filenames in scandir.walk(download_path):
                for filename in filenames:
                    self.root_checker[filename.lower().strip()] = True

        status = self.download_gallery_images(gallery_url,
                                              download_path,
                                              options,
                                              status,
                                              root=root)

        return status

    #
    #   Download Gallery
    #
    def download_gallery_images(self,
                                gallery_url,
                                download_path,
                                options,
                                status,
                                root=False):
        """
            Download images from a deviantart gallery
        """
        #
        #   Download and process the webpage
        current_skips = 0
        subfolder_data = common.fetch_webpage(session=self.session,
                                              url=gallery_url, timeout=60)
        subfolder = BeautifulSoup(subfolder_data)

        if gallery_url.find("?offset") == -1:
            print "\n\tProcessing Gallery - %30s" % (gallery_url),
        else:
            print "R",

        links = subfolder.find_all('a', {'class': 'thumb',
                                         'data-super-img': True})
        for xlink in links:
            if options.downloadlimit > 0 and \
                    status.return_downloads() >= options.downloadlimit:
                print "X"
                return status
            image_file = xlink["data-super-img"]
            file_to_download = image_file.replace("-t", "").strip()
            file_to_download = common.clean_filename(
                file_to_download,
                max_length=240)
            #
            #   Does directory exist?  If not create it
            #
            if not os.path.exists(
                    download_path):
                os.makedirs(download_path)

                #
                #       Check for file already existing,
                #        if so, don't download
                #
            if root and os.path.split(file_to_download)[1].lower().strip() in\
                self.root_checker:
                status.add_skipped(filename=file_to_download,
                                   options=options)
                current_skips += 1
                if options.skiplimit != 0 and \
                    current_skips >= options.skiplimit:
                    print "S"
                    return status
                continue

            if os.path.exists(
                    download_path +  # + gallery_name + os.sep +
                    os.path.split(file_to_download)[1]):
                status.add_skipped(filename=file_to_download,
                                   options=options)
                current_skips += 1
                if options.skiplimit != 0 and \
                    current_skips >= options.skiplimit:
                    print "S"
                    return status
            else:
                if common.download_file(
                        session=self.session,
                        url=file_to_download,
                        filename=os.path.split(file_to_download)[1],
                        download_folder=download_path,
                        timeout=45):
                    status.add_download(filename=file_to_download,
                                        options=options)
                else:
                    status.add_error(filename=file_to_download,
                                     options=options)
        time.sleep(.10)

        next_data = subfolder.find_all('li', {'class': 'next'})
        if next_data:
            next_data = next_data[0].find("a", {"class": "away"})
            if next_data != None:
                next_data = next_data.get("href")
                next_gallery_url = \
                    gallery_url[0:(gallery_url.find(r"/gallery"))]\
                    + next_data
                time.sleep(.5)
                status = self.download_gallery_images(next_gallery_url,
                                                      download_path,
                                                      options,
                                                      status,
                                                      root=root)
        return status

    def plugin_run(self):
        """
            meta function for plugin
        """
        pass

#
#   Add empty folder support
#
#   e.g. http://amazonmandy.deviantart.com/gallery/41236523
#
