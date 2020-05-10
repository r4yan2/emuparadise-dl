#!/usr/bin/env python3

from emuparadise_dl.helper import print_progress, flatten, tabulate
import requests
from bs4 import BeautifulSoup
import sys
import os
import time
import json
from termcolor import colored

# Disable InsecureRequestWarning to avoid complaints for some Backend
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Backend:
    base_url = ""
    search_url = ""
    search_params = {}
    download_url = ""
    download_params = {}
    association = {}

    def query(self, gid):
        return self.association.has_key(gid)

class TheEyeBackend(Backend):
    base_url = "https://the-eye.eu"
    search_url = "https://the-eye.eu/search"
    download_url = "https://the-eye.eu"

    def search(self, query):
        global rom_identifier
        self.search_params['s'] = query
        r = requests.get(self.search_url, params = self.search_params)
        soup = BeautifulSoup(r.text, 'html.parser')
        roms = []
        for tr in soup.find_all('tr')[1:]:
            rom, filetype, size = tr.find_all('th')
            rom_identifier += 1
            link = rom.a.get('href')
            device = link.split('/')[3]
            name = rom.text
            size = size.text
            self.association[rom_identifier] = requests.utils.quote(link)
            roms.append([rom_identifier, name, device, size])
        return roms

    def get_request(self, gid, cheaders):
        try:
            return requests.get(self.download_url + self.association[gid], params=self.download_params, headers=cheaders, stream=True, verify=False, allow_redirects=True)
        except KeyError:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)


class EmuparadiseBackend(Backend):
    base_url = "https://www.emuparadise.me"
    search_url = "https://www.emuparadise.me/roms/search.php"
    download_url = "http://direct.emuparadise.me/roms/get-download.php"

    def search(self, query):
        global rom_identifier
        self.search_params['query'] = query
        self.search_params['section'] = "roms"
        self.search_params['sysid'] = "0"
        r = requests.get(self.search_url, params=self.search_params)
        soup = BeautifulSoup(r.text, 'html.parser')
        rom_box = soup.findAll('div', attrs={'class':'roms'})
        roms = []
        for rom in rom_box:
            rom_identifier += 1
            gid = rom.find(href=True)['href'].split("/")[-1]
            self.association[rom_identifier] = gid
            name, tail = rom.text.split("System:")
            device, size = tail.split("Size:")
            for x in [name, device, size]:
                x = x.strip()
            #table = [list(flatten([[rom.find(href=True)['href'].split("/")[-1], [elems.get_text() for elems in rom.findAll('a')], rom.br.contents[5]]])) for rom in rom_box]
            roms.append([rom_identifier, name, device, size])
        return roms

    def get_request(self, gid, cheaders):
        try:
            self.download_params['gid'] = self.association[gid]
        except KeyError:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)

        self.download_params['test'] = 'true'
        
        r = requests.get(self.download_url, params=self.download_params, headers=cheaders, stream=True, verify=False, allow_redirects=True)
        return r

class RomsmaniaBackend(Backend):
    base_url = "https://romsmania.cc"
    search_url = "https://romsmania.cc/search"
    download_url = "https://romsmania.cc/download"

    def search(self, query):
        global rom_identifier
        base_url = "https://romsmania.cc"
        self.search_params['name'] = query
        r = requests.get(self.search_url, params = self.search_params)
        soup = BeautifulSoup(r.text, 'html.parser')

        roms = []
        for tr in soup.tbody.find_all('tr'):
            rom, system, rating, downs = tr.find_all('td')
            rom_identifier += 1
            self.association[rom_identifier] = rom.a.get('href')[len(base_url):]
            system = system.a.get('href').split('/')[-1]
            # Unfortunately Size isn't available
            # while searching so we just display NA
            roms.append([rom_identifier, rom.a.text, system, "-NA-"])
        return roms

    def get_request(self, gid, cheaders):
        try:
            r = requests.get(self.download_url + self.association[gid])
        except KeyError:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)
        s = BeautifulSoup(r.text, 'html.parser')
        return requests.get(s.find_all(attrs={"class":"wait__link"})[0].get('href'), headers=cheaeder, allow_redirects=True, verify=False, stream=True)

class DaromsBackend(Backend):
    base_url = "http://daroms.com"
    search_url = "http://daroms.com/api/search"
    download_url = "http://bingbong.daroms.com/daroms-gateway.php"

    def search(self, query):
        global rom_identifier
        self.search_params['params[category]']='false'
        self.search_params['params[term]']=query
        r = requests.post(self.search_url, data=self.search_params)
        roms = []
        for elem in r.json():
            rom_identifier += 1
            filename = elem['filename']
            size = elem['filesize']
            ID = int(elem['id'])
            key = requests.utils.unquote(elem['key'])
            device = elem['tags']
            self.association[rom_identifier] = (ID, key)
            roms.append([rom_identifier, filename, device, size])
        return roms

    def get_request(self, gid, cheaders):
        try:
            gid, key = self.association[gid]
        except KeyError:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)
        self.download_params['id'] = gid
        self.download_params['key'] = key
        return requests.get(self.download_url, params=self.download_params, headers=cheaders, stream=True, verify=False, allow_redirects=True)

class DoperomBackend(Backend):
    base_url = "https://www.doperoms.com"
    search_url = "https://www.doperoms.com/search.php"
    download_url = "http://doperoms.com:8080/files/"

    def search(self, query):
        global rom_identifier
        self.search_params['s'] = query
        r = requests.get(self.search_url, params=self.search_params, headers={'Accept-Encoding': 'identity'})
        s = BeautifulSoup(r.text, 'html.parser')

        roms = []
        for td in s.find_all('td', attrs={'height':'40'}):
            rom_identifier += 1

            link = td.find_all('a')[-1].get('href').split('.html')[0]
            name = td.find_all('a')[-1].text
            device = td.b.text
            self.association[rom_identifier] = link
            roms.append([rom_identifier, name, device, "-NA-"])
        return roms

    def get_request(self, gid, cheaders):
        try:
            return requests.get(self.download_url + self.association[gid], stream=True, allow_redirects=True, verify=False, headers={'Accept-Encoding': 'identity'}+cheaders)
        except KeyError:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)

class RomulationBackend(Backend):
    base_url = "https://www.romulation.net"
    search_url = "/roms/search"

    def search(self, query):
        global rom_identifier
        self.search_params['query'] = query
        r = requests.get(self.base_url + self.search_url, params=self.search_params)
        s = BeautifulSoup(r.text, 'html.parser')

        roms = []
        for tr in s.tbody.find_all('tr')[1:]:
            region, rom, downs, size = tr.find_all('td')
            
            region = region.text
            link = rom.a.get('href')
            device = rom.text[rom.text.find("[")+1:rom.text.find("]")]
            rom = rom.text[len(device)+3:]

            reason = "" 
            if len(size.find_all('i', attrs={'class': 'locked'})) > 0:
                reason = "is locked for guest users on romulation.net"

            size = size.text.strip()
            checksize = float(size.split(' ')[0])

            if ((size[-2] == 'G') or ((size[-2] == 'M') and (checksize > 200))):
                reason = "maximum size allowed for guest users on romulation.net is 200M"
            
            if reason != "":
                print(colored("Omitting", "red"), rom, "because", reason)
                continue
            rom_identifier += 1
            self.association[rom_identifier] = link
            roms.append([rom_identifier, rom + region, device, size])
        return roms

    def get_request(self, gid, cheaders):
        try:
            r = requests.get(self.base_url + self.association[gid])
        except KeyError:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)
        s = BeautifulSoup(r.text, 'html.parser')
        link = s.find('a', attrs={'class':'btn-yellow'}).get('href')
        r = requests.get(self.base_url + link)
        s = BeautifulSoup(r.text, 'html.parser')
        link = s.find('a', attrs={'class':'btn-yellow'}).get('href')
        return requests.get(link, headers=cheaders, allow_redirects=True, stream=True, verify=False)
    
def search_action(args):

    global rom_identifier
    rom_identifier = 0
    if args.all:
        b = backends.values()
    else:
        b = [backends[args.backend]]

    num_results = 0
    for backend in b:
        backend = backend()
        table = backend.search(args.query)
        if len(table) == 0:
            print("No results on", colored(backend.base_url, 'cyan'))
            continue
        else:
            num_results += len(table)
        if args.category != '':
            table = [[ids, name, system, size] for ids, name, system, size in table if args.category in system]
        tabulate(table, ["ID", "Name", "System", "Size"], max_width=args.maxwidth, title="Results from "+colored(backend.base_url, 'cyan'))

    if (num_results == 0):
        print("Sorry, no results!")
        sys.exit(0)
    ID = input("Found " + str(num_results) + " results!\nDo you want to download something? Enter the ID (multiple ID not supported) (N/Ctrl+c to cancel):\t")
    
    if (ID in ['n', 'N']):
        sys.exit(0)
    try:
        ID = int(ID)
    except:
        print("ID not understood, sorry.")
        sys.exit(0)
    if args.all:
        found = False
        for backend in b:
            backend = backend()
            found = backend.query(gid)
            if found:
                break
        if not found:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)

    else:
        backend = b[0]()
    downloader(backend, ID, args.output_directory, table[ID-1][1])


def downloader(backend, gid, directory, filename):

    c_size = 1024

    resume = False
    last_chunk = 0
    dl = 0
    resume_header = None
    if (directory != "") and (directory[-1] != "/"):
        directory = directory + "/"

    if os.path.exists(filename):
        print(filename, "already downloaded!\nExiting...")
        sys.exit(0)

    filename_partial = filename + ".partial"

    header = {}

    if os.path.exists(filename_partial):
        dl = os.path.getsize(filename_partial)
        last_chunk = int(dl/c_size)
        header['Range'] = 'bytes=%d-' % c_size * last_chunk
        print(filename, " already present, resuming...")
        resume = True
        fd = open(filename_partial, 'ab')
        #fd.seek(c_size * last_chunk, 0)
    else:
        print("Fetching from ", colored(backend.base_url, "cyan"), colored("Please consider supporting the site!", "green"))
        fd = open(filename_partial, "wb")

    r = backend.get_request(gid, header)
    realname = requests.utils.unquote(r.url.split('/')[-1])
    total_length = r.headers.get('content-length')
    total_length = int(total_length)
    
    st = os.statvfs("./")
    if total_length > (st.f_bavail * st.f_frsize):
        print("No more space on disk ", realname , " needs ", total_length/(1024*1024), " MB on disk!\nSkipping Download.")
        sys.exit(0)
 
    print_progress(0, total_length, prefix = realname, suffix = 'Speed', bar_length = 50)
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
        print_progress(dl, total_length, prefix = realname, suffix = suffix, bar_length = 50)
    fd.close()
    os.rename(filename_partial, realname)

def download_action(args):

    for backend in backend.values():
        backend = backend()
        gid = backend.match(url)
        if gid != None:
            break
    downloader(backend, gid, filename)
    sys.exit(0)


backends = {
        "emuparadise": EmuparadiseBackend,
        "the-eye": TheEyeBackend,
        "daroms": DaromsBackend,
        "romsmania": RomsmaniaBackend,
        #"doperom": DoperomBackend,
        #"romulation": RomulationBackend
            }
