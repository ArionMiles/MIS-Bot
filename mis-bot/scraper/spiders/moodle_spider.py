#!/usr/local/bin/python3
import os
import base64
from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
import scrapy.crawler as crawler
from twisted.internet import reactor
from multiprocessing import Process, Queue
from ..items import LecturesItem, PracticalsItem
from scrapy_splash import SplashRequest

from configparser import ConfigParser
# Read settings from config file
config = ConfigParser()
config.read('creds.ini')
SPLASH_INSTANCE = config.get('BOT', 'SPLASH_INSTANCE')

xpaths=[
    {"name": "AM", "query": "//table[1]/tr[3]/td[4]/", "is_practical":False},
    {"name": "AP", "query": "//table[1]/tr[4]/td[4]/", "is_practical":False},
    {"name": "AC", "query": "//table[1]/tr[5]/td[4]/", "is_practical":False},
    {"name": "EM", "query": "//table[1]/tr[6]/td[4]/", "is_practical":False},
    {"name": "BEE", "query": "//table[1]/tr[7]/td[4]/", "is_practical":False},
    {"name": "EVS", "query": "//table[1]/tr[8]/td[4]/", "is_practical":False},
    {"name": "Overall", "query": "//center/h2/u//text()", "clean":lambda values: "".join(values).strip(), "check_for_red":False, "is_practical":False},
    {"name": "total_lec_conducted", "query": "//table[1]/tr[last()]/td[2]/b/text()", "check_for_red":False, "is_practical":False, "is_practical":False},
    {"name": "total_lec_attended", "query": "//table[1]/tr[last()]/td[3]/b/text()", "check_for_red": False, "is_practical":False, "is_practical":False},
    {"name": "AC_prac", "query": "//table[2]/tr[2]/td[4]/", "is_practical":True},
    {"name": "AM_prac", "query": "//table[2]/tr[3]/td[4]/", "is_practical":True},
    {"name": "AP_prac", "query": "//table[2]/tr[4]/td[4]/", "is_practical":True},
    {"name": "BEE_prac", "query": "//table[2]/tr[5]/td[4]/", "is_practical":True},
    {"name": "Workshop", "query": "//table[2]/tr[6]/td[4]/", "is_practical":True},
    {"name": "EM_prac", "query": "//table[2]/tr[7]/td[4]/", "is_practical":True},
    {"name": "Overall_prac", "query": "//label/h2/", "is_practical":True}
]

class AttendanceSpider(InitSpider):
    name = 'attendance'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/student_page.php'
    start_urls = ['http://report.aldel.org/student/attendance_report.php']

    def __init__(self, USERNAME, PASSWORD, *args, **kwargs):
       super(AttendanceSpider, self).__init__(*args, **kwargs)
       self.USERNAME = USERNAME
       self.PASSWORD = PASSWORD
    
    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        return FormRequest.from_response(response,
                    formdata={'studentid': self.USERNAME, 'studentpwd': self.PASSWORD},
                    callback=self.check_login_response)

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in.
        """
        if self.USERNAME in response.body.decode():
            self.log("Login Successful!")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.log("Login failed! Check site status and credentials.")
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        url = 'http://report.aldel.org/student/attendance_report.php'
        splash_args = {
            'html': 1,
            'png': 1
        }

        yield SplashRequest(url, self.parse_result, endpoint='render.json', args=splash_args)

        yield LecturesItem(
            total_lec_conducted = response.xpath(xpaths['total_lec_conducted']).extract()[0].strip(),
            total_lec_attended = response.xpath(xpaths['total_lec_attended']).extract()[0].strip()
            )

    def parse_result(self, response):
        '''Store the screenshot'''
        imgdata = base64.b64decode(response.data['png'])
        filename = '{}_attendance.png'.format(self.USERNAME)
        with open(filename, 'wb') as f:
            f.write(imgdata)

'''    def parse(self, response):
        #Scrape attendance data from page

        lecture_kwargs = {}
        practicals_kwargs = {}
        def clean(values):
            return values[0].strip() if values else ""

        for xpath in xpaths:
            query = xpath['query']
            cleaner = xpath.get('clean', clean)

            if xpath.get('check_for_red', True):
                query = xpath['query'] + "text()"
                query2 = xpath['query'] + "font/u/b/text()"

                value1 = cleaner(response.xpath(query).extract())
                value2 = cleaner(response.xpath(query2).extract())
                value = value1 or value2
            else:
                value = cleaner(response.xpath(query).extract())

            if xpath["is_practical"]:
                practicals_kwargs[xpath["name"]] = str(value).strip()
            else:
                lecture_kwargs[xpath["name"]] = value

        yield LecturesItem(**lecture_kwargs)

        yield PracticalsItem(**practicals_kwargs)
'''

def scrape_attendance(USERNAME, PASSWORD):
    '''Run the spider multiple times, without hitting ReactorNotRestartable.Forks own process.'''
    def f(q):
        try:
            runner = crawler.CrawlerRunner({
        'ITEM_PIPELINES': {'scraper.pipelines.AttendancePipeline': 300,},
        
        'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                   'scrapy_splash.SplashMiddleware': 725,
                                   'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,},

        'SPLASH_URL':SPLASH_INSTANCE,
        'SPIDER_MIDDLEWARES':{'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
        'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
        })
            deferred = runner.crawl(AttendanceSpider, USERNAME=USERNAME, PASSWORD=PASSWORD)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)

    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result