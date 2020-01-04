class RomulationBackend(scrapy.Spider):
    base_url = "https://www.romulation.net"
    search_url = "/roms/search"

    def start_requests(self):
        formdata={
            'query': self.query,
            }
        return [scrapy.FormRequest(
                self.base_url + self.search_url+urlencode(formdata),
                callback=self.search,
                )]

    def search(self, body.fresponse):
        for tr in response.css('tbody').css('tr')[1:]:
            region, rom, downloaded, size = tr.css('td')
            link = rom.css('a::attr("href")').get()
            device, rom = re.findall('(\[\w+\])(.+)', rom.css('a::text').get())
            reason = "" 
            if size.css('.locked'):
                reason = "is locked for guest users on romulation.net"

            size = size.size.css('td::text').get().strip()
            checksize = float(size.split(' ')[0])

            if ((size[-2] == 'G') or ((size[-2] == 'M') and (checksize > 200))):
                reason = "maximum size allowed for guest users on romulation.net is 200M"
            if reason != "":
                print(colored("Omitting", "red"), rom, "because", reason)
                continue
            yield {
                'gid':link
                'name': rom + region, 
                'device': device, 
                'size': size
                }

    @classmethod
    def get_request(cls, gid, cheaders):
        r = requests.get(cls.base_url + gid)
        s = BeautifulSoup(r.text, 'html.parser')
        link = s.find('a', attrs={'class':'btn-yellow'}).get('href')
        r = requests.get(cls.base_url + link)
        s = BeautifulSoup(r.text, 'html.parser')
        link = s.find('a', attrs={'class':'btn-yellow'}).get('href')
        return requests.get(link, headers=cheaders, allow_redirects=True, stream=True, verify=False)


