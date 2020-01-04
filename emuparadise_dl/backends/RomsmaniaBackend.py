class RomsmaniaBackend(scrapy.Spider):
    base_url = "https://romsmania.cc"
    search_url = "https://romsmania.cc/search"
    download_url = "https:/romsmania.cc/download"

    def start_requests(self):
        formdata={
            'name': self.query,
        }
        return [scrapy.FormRequest(
                self.search_url+urlencode(formdata),
                callback=self.search,
                )]


    def search(self, response):
        for tr in response.css('tbody').css('tr'):
            rom, system, rating, downloaded = tr.css('td')[0]
            link = rom.css('a::attr("href")').get()[len(base_url):]
            name = rom.css('a::text').get()
            system = system.css('a::text').get()   
            # Unfortunately Size isn't available
            # while searching so we just display NA
            roms.append([rom_identifier, rom.a.text, system, "-NA-"])
            yield {
                'gid': link,
                'name': name,
                'system': system,
                'size': '-NA-'
            }

    @classmethod
    def get_request(cls, gid, cheaders):
        r = requests.get(cls.download_url + gid)
        s = BeautifulSoup(r.text, 'html.parser')
        return requests.get(
            s.find_all(attrs={"class":"wait__link"})[0].get('href'), 
            headers=cheaeder, 
            allow_redirects=True, 
            verify=False, 
            stream=True)


