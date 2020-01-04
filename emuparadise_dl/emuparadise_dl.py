#!/usr/bin/env python3

# Scrapy
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from emuparadise_dl.helper import print_progress, flatten, tabulate
from emuparadise_dl.dbm import *
from emuparadise_dl.backends import *
import requests
import sys
import os
import time
import json
from termcolor import colored
import operator

# Disable InsecureRequestWarning to avoid complaints for some Backend
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class StorePipeline(object):

    def open_spider(self, spider):
        spider.dbm.create(spider)

    def process_item(self, item, spider):
        spider.dbm.write(spider, item)

class EmuparadiseDL():

    def __init__(self):
        self.dbm = MemoryDBM()

    def search_action(self, args):
        if args.all:
            b = backends.values()
        else:
            b = [backends[args.backend]]
    
        num_results = 0
        for backend in b:
            Settings = get_project_settings()
            Settings['ITEM_PIPELINES'] = {'emuparadise_dl.emuparadise_dl.StorePipeline': 100}
            Settings['LOG_ENABLED'] = False
            process = CrawlerProcess(Settings)
            process.crawl(backend, query=args.query, dbm=self.dbm)
            process.start()
            table = self.dbm.get_results(backend) 
            if len(table) == 0:
                print("No results on", colored(backend.base_url, 'cyan'))
                continue
            else:
                num_results += len(table)
            table = [(gid,name,system,size) for gid,name,system,size in table if args.category == '' or re.search(args.category, system)]
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
        backend, real_id = self.dbm.query(ID)
        if not backend:
            print("ID not present, Please double check and if it's not a mistake fill a bug report!")
            sys.exit(0)
        self.downloader(backend, real_id, args.output_directory, table[ID-1][1])
    
    
    def downloader(self, backend, gid, directory, filename):
    
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
    
    def download_action(self, args):
    
        for backend in backend.values():
            backend = backend()
            gid = backend.match(url)
            if gid != None:
                break
        self.downloader(backend, gid, filename)
        sys.exit(0)

backends = {
        "emuparadise": EmuparadiseBackend,
        "the-eye": TheEyeBackend,
        "daroms": DaromsBackend,
        "romsmania": RomsmaniaBackend,
        "doperom": DoperomBackend,
        "romulation": RomulationBackend,
}
