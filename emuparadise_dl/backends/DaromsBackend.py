class DaromsBackend(scrapy.Spider):
    base_url = "http://daroms.com"
    search_url = "http://daroms.com/api/search"
    download_url = "http://bingbong.daroms.com/daroms-gateway.php"

    def start_requests(self):
        formdata={
            'params[category]': 'false',
            'params[term]' :query,
        }
        return [scrapy.FormRequest(
                self.search_url+urlencode(formdata),
                callback=self.search,
                )]

    def search(self, response):
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

    @classmethod
    def get_request(self, gid, cheaders):
        gid, key = self.association[gid]
        self.download_params['id'] = gid
        self.download_params['key'] = key
        return requests.get(self.download_url, params=self.download_params, headers=cheaders, stream=True, verify=False, allow_redirects=True)


