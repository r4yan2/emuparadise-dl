#!/usr/bin/python3

from helper import print_progress, signal_handler, flatten, tabulate, check_connection
import argparse
import requests
from bs4 import BeautifulSoup
import sys
import signal
import os
import time
import json

# Disable InsecureRequestWarning to avoid complaints for some Backend
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Backend:
    base_url = ""
    search_url = ""
    search_params = {}
    download_url = ""
    download_params = {}

class TheEyeBackend(Backend):
    base_url = "https://the-eye.eu"
    search_url = "https://the-eye.eu/search"
    download_url = "https://the-eye.eu"
    association = {}

    def search(self, query):
        self.search_params['s'] = query
        r = requests.get(self.search_url, params = self.search_params)
        soup = BeautifulSoup(r.text, 'html.parser')
        i = 0
        roms = []
        for tr in soup.find_all('tr')[1:]:
            rom, filetype, size = tr.find_all('th')
            i += 1
            link = rom.a.get('href')
            device = link.split('/')[3]
            name = rom.text
            size = size.text
            self.association[i] = requests.utils.quote(link)
            roms.append([i, name, device, size])
        return roms

    def get_request(self, gid):
        return requests.get(self.download_url + self.association[gid], params=self.download_params, stream=True, verify=False, allow_redirects=True)


class EmuparadiseBackend(Backend):
    base_url = "https://www.emuparadise.me"
    search_url = "https://www.emuparadise.me/roms/search.php"
    download_url = "http://direct.emuparadise.me/roms/get-download.php"

    def search(self, query):
        self.search_params['query'] = query
        self.search_params['section'] = "roms"
        self.search_params['sysid'] = "0"
        r = requests.get(self.search_url, params=self.search_params)
        soup = BeautifulSoup(r.text, 'html.parser')
        rom_box = soup.findAll('div', attrs={'class':'roms'})
        table = [list(flatten([[rom.find(href=True)['href'].split("/")[-1], [elems.get_text() for elems in rom.findAll('a')], rom.br.contents[5]]])) for rom in rom_box]
        return table

    def get_request(self, gid):
        self.download_params['gid'] = gid
        self.download_params['test'] = 'true'
        
        r = requests.get(self.download_url, params=self.download_params, stream=True, verify=False, allow_redirects=True)
        return r

class RomsmaniaBackend(Backend):
    base_url = "https://romsmania.cc"
    search_url = "https://romsmania.cc/search"
    download_url = "https://romsmania.cc/download"
    association = {}

    def search(self, query):
        base_url = "https://romsmania.cc"
        self.search_params['name'] = query
        r = requests.get(self.search_url, params = self.search_params)
        soup = BeautifulSoup(r.text, 'html.parser')

        roms = []
        i = 0
        for tr in soup.tbody.find_all('tr'):
            rom, system, rating, downs = tr.find_all('td')
            i += 1
            self.association[i] = rom.a.get('href')[len(base_url):]
            system = system.a.get('href').split('/')[-1]
            # Unfortunately Size isn't available
            # while searching so we just display NA
            roms.append([i, rom.a.text, system, "-NA-"])
        return roms

    def get_request(self, gid):
        print(self.download_url + self.association[gid])
        r = requests.get(self.download_url + self.association[gid])
        s = BeautifulSoup(r.text, 'html.parser')
        return requests.get(s.find_all(attrs={"class":"wait__link"})[0].get('href'), allow_redirects=True, verify=False, stream=True)

class DaromsBackend(Backend):
    base_url = "http://daroms.com"
    search_url = "http://daroms.com/api/search"
    download_url = "http://bingbong.daroms.com/daroms-gateway.php"
    association={}

    def search(self, query):
        self.search_params['params[category]']='false'
        self.search_params['params[term]']=query
        r = requests.post(self.search_url, data=self.search_params)
        roms = []
        for elem in r.json():
            filename = elem['filename']
            size = elem['filesize']
            ID = int(elem['id'])
            key = requests.utils.unquote(elem['key'])
            device = elem['tags']
            self.association[ID] = key
            roms.append([ID, filename, device, size])
        return roms

    def get_request(self, gid):
        self.download_params['id'] = gid
        self.download_params['key'] = self.association[gid]
        return requests.get(self.download_url, params=self.download_params, stream=True, verify=False, allow_redirects=True)
    
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

def search_action(args):
    backend = backends[args.backend]()
    print("Using", backend.base_url, "as backend. Please consider supporting the site!")
    table = backend.search(args.query)
    if len(table) == 0:
        print("Sorry, no results!")
        sys.exit(0)
    if args.category != '':
        table = [[ids, name, system, size] for ids, name, system, size in table if args.category in system]
    tabulate(table, ["ID", "Name", "System", "Size"], max_width=args.maxwidth)

    ID = input("Do you want to download something? Enter the ID (multiple ID not supported) (N/Ctrl+c to cancel):\t")
    
    if (ID in ['n', 'N']):
        sys.exit(0)
    try:
        ID = int(ID)
    except:
        print("ID not understood, sorry.")
        sys.exit(0)
    downloader(backend, int(ID))

def check_filename(filename):
    if os.path.exists(filename):
        print(filename, "already downloaded!\nExiting...")
        sys.exit(0)

def downloader(backend, gid):

    c_size = 1024

    resume = False
    last_chunk = 0
    dl = 0
    resume_header = None
    if (args.output_directory != "") and (args.output_directory[-1] != "/"):
        args.output_directory = args.output_directory + "/"

    r = backend.get_request(gid)
    filename = requests.utils.unquote(r.url.split('/')[-1])
    check_filename(filename)
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

backends = {
        "emuparadise": EmuparadiseBackend,
        "the-eye": TheEyeBackend,
        "daroms": DaromsBackend,
        "romsmania": RomsmaniaBackend
            }

parser = argparse.ArgumentParser(description=long_desc)
subparser = parser.add_subparsers(help='sub-command help')

search = subparser.add_parser('search')#, aliases=['s'])
search.add_argument('-b', '--backend', default='emuparadise', help='specify backend to search, by default all are used, to known the list of supported backend do "emuparadise-dl list"')
search.add_argument('-c', '--category', default='', help='search for a specific system')
search.add_argument('-o', '--output-directory', default='', help='select destination directory', action=CheckAction)
search.add_argument('--maxwidth', type=int, default=80, help='set the maximum width a single column should occupy')
search.add_argument('query', help='a quoted string to search, ex. "resident evil"')
search.set_defaults(func=search_action)

download = subparser.add_parser('download')#, aliases=['d'])
download.add_argument('-u', '--url', help='provide url of the file to download instead of ID', action='store_true')
download.add_argument('-o', '--output-directory', default='', help='select destination directory', action=CheckAction)
download.add_argument('ID', nargs='+', help='ID of the file to download')
download.set_defaults(func=download_action)

listing = subparser.add_parser('list')
listing.set_defaults(func=lambda x: print("Available backends: ", ", ".join(backends.keys())))

args = parser.parse_args()
args.func(args)
