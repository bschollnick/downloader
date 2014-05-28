"""
    Downloader, mass file downloader.
"""
import common
import logging, logging.handlers
import os
import os.path
import plistlib
import stat
import sys
from optparse import OptionParser
from yapsy.PluginManager import PluginManager

script_filename = os.path.abspath(sys.argv[0])
script_directory = os.sep.join(os.path.split(script_filename)[0:-1])

def initialize_parser():
    """
    Initialize the parser, and set the basic parser options
    """
    parser = OptionParser(usage="usage: %prog [options] filename", 
                          version="%prog 1.0")
    parser.add_option("-u", "--url",
                      action="store",
                      dest="url_to_fetch",
                      default="",
                      help="URL to fetch")

    parser.add_option("-t", "--target",
                      action="store", 
                      dest="download_folder",
                      default="",
                      help="Download Folder to use",)

    parser.add_option("--details",
                      action="store_true",
                      dest="details",
                      default=False,
                      help="Report details on downloads",)

    parser.add_option("--silent",
                      action="store_true",
                      dest="silent",
                      default=False,
                      help="Absolutely no feedback on downloading",)

    parser.add_option("--dllimit",
                      action="store", 
                      dest="downloadlimit",
                      default=0,
                      type="int",
                      help="Maximum # of Files to download before quitting",)

    parser.add_option("--skiplimit",
                      action="store", 
                      dest="skiplimit",
                      default=0,
                      type="int",
                      help="Maximum # of Files to skip before quitting",)

    parser.add_option("--start",
                      action="store", 
                      dest="startingplace",
                      default=0,
                      type="int",
                      help="The Offset to start at",)
                      
    return parser

def plugin_parser_adds(parser, plugin):
    """
        Call the parser options from the plugin(s), 
        to allow the plugins to install
        options into the parser.
    """
    if hasattr(plugin, "parser_options"):
        parser = plugin.parser_options(parser)
    
def parse_commandline(parser):
    """
        Process the parser and return the options to the main.
    """
    (options, args) = parser.parse_args()
    return options

def make_weblocation_file(filename, 
                          url):
    """
    Make the weblocation file, to allow easy "one click" access 
    to the gallery, etc, that originated the content.
    """
    if not os.path.exists(filename):
        try:
            output_file = open(filename, "w")
            pl = dict(URL=url)
            plistlib.writePlist(pl, output_file)
            output_file.close()
        except IOError:
            pass

def make_script_file(options):  
    """
    Make the shellscript file, to help automate redownload of the content.
    """
    try:
        script_name = "update_capture.command"
        if not os.path.exists (options.download_folder +
                               os.sep + script_name):
            update_script = open(options.download_folder +
                                 os.sep + script_name,
                                 "w")
            update_script.write("python %s " % script_filename)
            for x in sys.argv[1:]:
                update_script.write('"%s"' % x + " ")
            update_script.close()
            os.chmod(options.download_folder + os.sep + script_name, 
                     511 | stat.S_IEXEC)
    except IOError:
        pass
    
def main():   
    """
        The main function. TaDa!
    """
    # Load the plugins from the plugin directory.
    manager = PluginManager()
    manager.setPluginPlaces([script_directory + os.sep + "plugins"])
    manager.collectPlugins()

    parser = initialize_parser()
    plugin_names = {}
    # Loop round the plugins and print their names.
    for plugin in manager.getAllPlugins():
        plugin_names[plugin.name.lower().strip()] = plugin
            # plugin name contains pointer to module
        plugin_parser_adds(parser, plugin.plugin_object)

    options = parse_commandline(parser)
    if options.silent:
        print options
    if options.url_to_fetch == "":
        print "Please supply an URL to process."
        return None

    if options.download_folder == "":
        print "Please supply an download folder."
        return None
    
    options.download_folder = os.path.abspath(options.download_folder)
    options.download_folder = common.clean_filename(\
        unicode(options.download_folder))

    if not options.download_folder.strip().endswith(os.sep):
        options.download_folder = options.download_folder + os.sep
    
    #
    #   Make Root download folder
    #
    if os.path.exists(options.download_folder) != True:
        os.makedirs(options.download_folder)

    make_script_file(options)   
    make_weblocation_file(options.download_folder +
                          os.sep + "downloaded_site.webloc",
                          options.url_to_fetch)

    if not options.silent:
        print "Downloading to: %s" % options.download_folder

    for x in plugin_names.keys():
        print "Checking Plugin - %s" % x
        if getattr(options, x):
            plugin = plugin_names[x].plugin_object
            print "Using Plugin - %s" % x

    (total_downloaded, total_skipped, total_errors) = plugin.download(options)
    print
    print "Total Downloaded Files - %s" % total_downloaded
    print "Total Skipped Files - %s" % total_skipped
    print "Total Errors - %s" % total_errors
    

if __name__ == "__main__":
    my_logger = logging.getLogger("yapsy")
    handler = logging.handlers.RotatingFileHandler("download_log.txt",
                                                   backupCount=5,
                                                   maxBytes=1024*1024)
    my_logger.addHandler(handler)
    logging.getLogger('yapsy').setLevel(logging.DEBUG)
    print "main"
    main()
