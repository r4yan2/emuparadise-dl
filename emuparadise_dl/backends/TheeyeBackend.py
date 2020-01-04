class TheEyeBackend(scrapy.Spider):
    base_url = "https://the-eye.eu"
    search_url = "https://the-eye.eu/search"
    download_url = "https://the-eye.eu"

    def start_request(self):
        formdata = {'s': self.query}
        return [scrapy.FormRequest(
            self.search_url + urlencode(formdata),
            callback=self.search)]

    def search(self, response):
        for tr in request.xpath('tr').getall()[1:]:
            rom, filetype, size = tr.find_all('th')
            link = rom.css('a::attr("href")')
            device = link.get().split('/')[3]
            name = rom.get.strip()
            size = size.get().strip()
            yield {
                'gid': urlencode(link), 
                'name' : name, 
                'system' : device,
                'size': size,
                }
        
    @classmethod
    def get_request(cls, gid, cheaders):
        return requests.get(cls.download_url + gid, params=self.download_params, headers=cheaders, stream=True, verify=False, allow_redirects=True)


