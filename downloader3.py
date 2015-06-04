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
import time
from optparse import OptionParser
from yapsy.PluginManager import PluginManager

SCRIPT_FILENAME = os.path.abspath(sys.argv[0])
SCRIPT_DIRECTORY = os.sep.join(os.path.split(SCRIPT_FILENAME)[0:-1])

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

    parser.add_option("-l", "--log",
                      action="store",
                      dest="log_folder",
                      default="",
                      help="The Log Folder to use",)

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


    parser.add_option("--csv",
                      action="store",
                      dest="csv_file",
                      default="",
                      help="CSV File containing sources")
    return parser

def plugin_parser_adds(parser, plug):
    """
        Call the parser options from the plugin(s),
        to allow the plugins to install
        options into the parser.
    """
    if hasattr(plug, "parser_options"):
        parser = plug.parser_options(parser)

def parse_commandline(parser):
    """
        Process the parser and return the options to the main.
    """
    options = parser.parse_args()[0]
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
            plist = dict(URL=url)
            plistlib.writePlist(plist, output_file)
            output_file.close()
        except IOError:
            pass

def make_script_file(options):
    """
    Make the shellscript file, to help automate redownload of the content.
    """
    try:
        script_name = "update_capture.command"
        if not os.path.exists(options.download_folder +
                              os.sep + script_name):
            update_script = open(options.download_folder +
                                 os.sep + script_name,
                                 "w")
            update_script.write("python %s " % SCRIPT_FILENAME)
            for x_arg in sys.argv[1:]:
                update_script.write('"%s"' % x_arg + " ")
            update_script.close()
            os.chmod(options.download_folder + os.sep + script_name,
                     511 | stat.S_IEXEC)
    except IOError:
        pass

def process_commandline():
    """
    Process the command line options
    """
    parser = initialize_parser()

    manager = PluginManager()
    manager.setPluginPlaces([SCRIPT_DIRECTORY + os.sep + "plugins"])
    manager.collectPlugins()

    plugin_names = {}
    # Loop round the plugins and print their names.
    for plug in manager.getAllPlugins():
        plugin_names[plug.name.lower().strip()] = plug
            # plugin name contains pointer to module
        plugin_parser_adds(parser, plug.plugin_object)

    options = parse_commandline(parser)

    if options.silent:
        print options

    if options.url_to_fetch == "":
        print "Please supply an URL to process."
        return None

    if options.download_folder == "":
        print "Please supply an download folder."
        return None

    if options.log_folder == "":
        options.log_folder = "~/logs"

    options.download_folder = os.path.abspath(options.download_folder)
    options.download_folder = common.clean_filename(\
        unicode(options.download_folder))

    if not options.download_folder.strip().endswith(os.sep):
        options.download_folder = options.download_folder + os.sep

    return (options, plugin_names)


def main():
    """
        The main function. TaDa!
    """
    log = logging.getLogger('Downloader')
    log.setLevel(logging.INFO)

    console_h = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(message)s')
    console_h.setFormatter(console_formatter)
    log.addHandler(console_h)

    s_options, plugin_names = process_commandline()
    logdir = os.path.abspath(os.path.join(\
        os.path.expanduser(s_options.log_folder)))
    print "Logging to ", logdir
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logfilename = os.path.abspath(os.path.join(logdir, "downloader.log"))
    print "Log file name: ", logfilename

    file_h = logging.handlers.RotatingFileHandler(logfilename,
                                                  maxBytes=(50000),
                                                  backupCount=7)
    file_format = logging.Formatter(\
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_h.setFormatter(file_format)
    log.addHandler(file_h)

    #
    #   Make Root download folder
    #
    if os.path.exists(s_options.download_folder) != True:
        os.makedirs(s_options.download_folder)

    for x_key in plugin_names.keys():
        if getattr(s_options, x_key):
            plugin = plugin_names[x_key].plugin_object
            print "Using Plugin - %s" % x_key

    start_time = time.time()
    if not s_options.silent:
        log.info("Downloading to: %s", s_options.download_folder)

    make_weblocation_file(s_options.download_folder +
                          os.sep + "downloaded_site.webloc",
                          s_options.url_to_fetch)

    results = plugin.download(s_options)
    elapsed = int((time.time() - start_time) * 100)/100

    if results != None:
        (total_downloaded, total_skipped, total_errors) = results

    print
    print
    log.info("Total Downloaded Files - %s", total_downloaded)
    log.info("Total Skipped Files - %s", total_skipped)
    log.info("Total Errors - %s", total_errors)
    log.info("Elapsed Time (Seconds) - %f", elapsed)
    log.info("Elapsed Time (Min) - %f", (elapsed/60))
    if total_downloaded != 0:
        sys.exit(1)
    else:
        sys.exit(0)    # Load the plugins from the plugin directory.



if __name__ == "__main__":
    main()
