import ConfigParser
from scrapy.contrib.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
#from scrapy.shell import inspect_response

CONFIG = ConfigParser.RawConfigParser()
CONFIG.read('C:/Users/Kanishk/Documents/Projects/MIS Bot/MIS/MIS/spiders/creds.ini')
USERNAME = CONFIG.get('MIS', 'USERNAME')
PASSWORD = CONFIG.get('MIS', 'PASSWORD')

xpath = {
    'AM_pcent': '//table[1]/tr[3]/td[4]/text()',
    'AP_pcent' : '//table[1]/tr[4]/td[4]/font/u/b/text()',
    'AC_pcent': '//table[1]/tr[5]/td[4]/font/u/b/text()',
    'EM_pcent': '//table[1]/tr[6]/td[4]/font/u/b/text()',
    'BEE_pcent': '//table[1]/tr[7]/td[4]/font/u/b/text()',
    'EVS_pcent': '//table[1]/tr[8]/td[4]/font/u/b/text()',
    'Overall': '//center/h2/u/b/text()'
}

class MySpider(InitSpider):
    name = 'mis'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/student_page.php'
    start_urls = ['http://report.aldel.org/student/attendance_report.php']
    #['file:///C:/Users/Kanishk/Documents/Projects/Moodle%20Bot/tutorial/attendance.php']
    #


    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        return FormRequest.from_response(response,
                    formdata={'studentid': USERNAME, 'studentpwd': PASSWORD},
                    callback=self.check_login_response)

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in.
        """
        if "117kanishk2033" in response.body:
            self.log("Successfully logged in. Let's start crawling!")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.log("Bad times :(")
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        '''Scrape data from page'''
        #inspect_response(response, self)
        #for item in response():
        yield {
            'Applied Mathematics': response.xpath(xpath['AM_pcent']).extract()[0].strip(),
            'Applied Physics' : response.xpath(xpath['AP_pcent']).extract(),
            'Applied Chemistry': response.xpath(xpath['AC_pcent']).extract(),
            'Engineering Mechanics': response.xpath(xpath['EM_pcent']).extract(),
            'BEE': response.xpath(xpath['BEE_pcent']).extract(),
            'EVS': response.xpath(xpath['EVS_pcent']).extract(),
            'Overall': response.xpath(xpath['Overall']).extract(),
        }
