#!/usr/bin/python3

import argparse
import requests
from bs4 import BeautifulSoup
import sys
#import urllib
import signal
import os
import re
import time

def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar

    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def signal_handler(sig, frame):
    sys.stdout.flush()
    print('You pressed Ctrl+C!')
    sys.exit(0)

def flatten(items, seqtypes=(list, tuple)):
    for i, x in enumerate(items):
        while i < len(items) and isinstance(items[i], seqtypes):
            items[i:i+1] = items[i]
    return items

class CheckAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not os.path.isdir(values):
            print("The supplied directory '"+ values +"' does not exists!\nDo you want to create it now? (Y/N)")
            if sys.stdin in ["y", "Y", "yes", "YES", "porcodio"]:
                os.mkdir(os.path.expanduser(values))
                setattr(namespace, self.dest, values)
            else:
                print("Ok, directory not created, exiting...")
                sys.exit(0)
        else:
            setattr(namespace, self.dest, values)

def tabulate(data, header, max_width=80, align='left'):
    if not all(map(lambda x: len(x) == len(header), data)):
        print("sorry, but the table is misbuild!")
    columns_width = [max([len(str(elem)) for elem in sublst]) for sublst in zip(*data)]
    print('| ' + ' + '.join(["-" * w for w in columns_width]) + '|')
    print('| ' + ' | '.join([h + ' ' * (columns_width[i] - len(h)) for i,h in enumerate(header)]) + '|')
    print('| ' + ' + '.join(["-"*w for w in columns_width]) + '|')
    for line in data:
        print('| ' + ' | '.join([str(d) + ' ' * (columns_width[i] - len(str(d))) for i,d in enumerate(line)]) + '|')
    print('| ' + ' + '.join(["-"*w for w in columns_width]) + '|')

def search_action(args):
    search_url = "https://www.emuparadise.me/roms/search.php"
    payload = {}
    payload['query'] = args.query
    payload['section'] = "roms"
    payload['sysid'] = "0"
    r = requests.get(search_url, params=payload)
    soup = BeautifulSoup(r.text, 'html.parser')
    rom_box = soup.findAll('div', attrs={'class':'roms'})
    table = [list(flatten([[rom.find(href=True)['href'].split("/")[-1], [elems.get_text() for elems in rom.findAll('a')], rom.br.contents[5]]])) for rom in rom_box]
    if len(table) == 0:
        print("Sorry, no results")
    if args.category != '':
        table = [[ids, name, system, size] for ids, name, system, size in table if re.match(args.category, system, re.IGNORECASE)]
    tabulate(table, ["ID", "Name", "System", "Size"], max_width=args.maxwidth)

    sys.exit(0)

def downloader(gid):

    download_url = "http://direct.emuparadise.me/roms/get-download.php"
    download_params = {}
    download_params['gid'] = gid
    download_params['test'] = 'true'
    
    c_size = 1024

    resume = False
    last_chunk = 0
    dl = 0
    resume_header = None
    r = requests.head(download_url, params=download_params, allow_redirects=True)
    if (args.output_directory != "") and (args.output_directory[-1] != "/"):
        args.output_directory = args.output_directory + "/"
    filename = args.output_directory + re.sub('%20', ' ', r.url.split('/')[-1]) #urllib.parse.unquote(r.url.split("/")[-1])

    if os.path.exists(filename):
        print(filename, "already downloaded!\nExiting...")
        sys.exit(0)

    filename_partial = filename + ".partial"
    total_length = r.headers.get('content-length')
    total_length = int(total_length)
    
    st = os.statvfs("./")
    if total_length > (st.f_bavail * st.f_frsize):
        print("No more space on disk ", filename , " needs ", total_length/(1024*1024), " MB on disk!\nSkipping Download.")
        return
    
    if os.path.exists(filename_partial):
        dl = os.path.getsize(filename_partial)
        last_chunk = int(dl/c_size)
        resume_header = {'Range': 'bytes=%d-' % c_size * last_chunk}
        print(filename, " already present, resuming...")
        resume = True
        fd = open(filename_partial, 'ab')
        #fd.seek(c_size * last_chunk, 0)
    else:
        print("Downloading...")
        fd = open(filename_partial, "wb")
    print_progress(0, total_length, prefix = filename, suffix = 'Speed', bar_length = 50)
    r = requests.get(download_url, headers=resume_header, params=download_params, stream=True, verify=False, allow_redirects=True)
    speed = 0
    start_time = epoch = time.time()
    KB = 1024
    MB = KB * 1024
    for data in r.iter_content(chunk_size=c_size):
        dl += len(data)
        fd.write(data)
        if (time.time() - epoch) > 1:
            epoch = time.time()
            speed = dl/(epoch-start_time)
        if (speed > MB):
            suffix = "{0:.2f}".format(speed/MB) + " MB/s\t"
        elif (speed > KB):
            suffix = "{0:.2f}".format(speed/KB) + " KB/s\t"
        else:
            suffix = str(speed) + "B/s\t"
        print_progress(dl, total_length, prefix = filename, suffix = suffix, bar_length = 50)
    fd.close()
    os.rename(filename_partial, filename)

def download_action(args):

    if args.url:
        for url in args.ID:
            downloader(int(re.sub("[^D]", args.ID.split('/')[-1])))
    else:
        for ID in args.ID:
            downloader(ID)
    
    print("...Done")
    sys.exit(0)

def check_connection():
    try:
        requests.head("http://google.com", allow_redirects=True)
        return True
    except :
        return False

signal.signal(signal.SIGINT, signal_handler)
if not check_connection():
    print("Sorry, no internet connection available")
    sys.exit()

long_desc = """
emuparadise-dl

Small utility to search and download roms from emuparadise.me now that
all links have been disabled.

To use the tool first search for something, than start the download providing
as input the correct ID for the rom you wish to have.
"""
parser = argparse.ArgumentParser(description=long_desc)
subparser = parser.add_subparsers(help='sub-command help')

search = subparser.add_parser('search')#, aliases=['s'])
search.add_argument('query', help='a quoted string to search, ex. "resident evil"')
search.add_argument('-c', '--category', default='', help='search for a specific system')
search.add_argument('--maxwidth', type=int, default=80, help='set the maximum width a single column should occupy')
search.set_defaults(func=search_action)
download = subparser.add_parser('download')#, aliases=['d'])
download.add_argument('ID', nargs='+', help='ID of the file to download')
download.add_argument('-u', '--url', help='provide url of the file to download instead of ID', action='store_true')
download.add_argument('-o', '--output-directory', default='', help='select destination directory', action=CheckAction)
download.set_defaults(func=download_action)
args = parser.parse_args()
args.func(args)
