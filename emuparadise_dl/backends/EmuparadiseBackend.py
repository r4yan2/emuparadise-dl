import scrapy
from urllib.parse import urlencode
import requests

class EmuparadiseBackend(scrapy.Spider):
    name = "porcodio"
    base_url = "https://www.emuparadise.me"
    search_url = "https://www.emuparadise.me/roms/search.php?"
    download_url = "http://direct.emuparadise.me/roms/get-download.php?"

    def start_requests(self):
        formdata={
            'query': self.query,
            'section': 'roms',
            'sysid': '0',
        }
        return [scrapy.Request(
                self.search_url+urlencode(formdata),
                callback=self.search,
                )]

    def search(self, response):
        rom_box = response.css('div.roms')
        roms = []
        import pudb;pu.db
        for rom in rom_box:
            gid = rom.css('a::attr("href")').get().split('/')[-1]
            name = rom.css('a::text').get().strip()
            device = rom.css('a.sysname::text').get().strip()
            size = rom.css('div.roms::text')[-1].get().strip()
            yield {
                'gid': gid,
                'name': name,
                'system': device,
                'size': size,
            }

    @classmethod
    def get_request(cls, gid, cheaders):
        download_params = {
            'gid': gid,
            'test': 'true',
        }
        
        r = requests.get(cls.download_url, params=download_params, headers=cheaders, stream=True, verify=False, allow_redirects=True)
        return r
