#!/usr/local/bin/python3
import os
import base64
from configparser import ConfigParser
from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
import scrapy.crawler as crawler
from twisted.internet import reactor
from multiprocessing import Process, Queue
from ..items import LecturesItem
from scrapy_splash import SplashRequest

# Read settings from config file
config = ConfigParser()
config.read('files/creds.ini')
SPLASH_INSTANCE = config.get('BOT', 'SPLASH_INSTANCE')

xpaths = {
    'total_lec_conducted': '//table[1]/tbody/tr[last()]/td[2]/b/text()',
    'total_lec_attended': '//table[1]/tbody/tr[last()]/td[3]/b/text()',
}

class AttendanceSpider(InitSpider):
    name = 'attendance'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/student_page.php'
    start_urls = ['http://report.aldel.org/student/attendance_report.php']

    def __init__(self, USERNAME, PASSWORD, chatID, *args, **kwargs):
       super(AttendanceSpider, self).__init__(*args, **kwargs)
       self.USERNAME = USERNAME
       self.PASSWORD = PASSWORD
       self.chatID = chatID
    
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
        successfully logged in."""
        if self.USERNAME in response.body.decode():
            self.logger.info("Login Successful!")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.logger.info("Login failed! Check site status and credentials.")
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        url = 'http://report.aldel.org/student/attendance_report.php'
        splash_args = {
            'html': 1,
            'png': 1
        }
        self.logger.info("Taking snapshot of Attendance Report...")
        yield SplashRequest(url, self.parse_result, endpoint='render.json', args=splash_args)

    def parse_result(self, response):
        '''Store the screenshot'''
        imgdata = base64.b64decode(response.data['png'])
        filename = 'files/{}_attendance.png'.format(self.USERNAME)
        with open(filename, 'wb') as f:
            f.write(imgdata)
            self.logger.info("Saved attendance report as: {}_attendance.png".format(self.USERNAME))

        yield LecturesItem(
            total_lec_conducted = response.xpath(xpaths['total_lec_conducted']).extract()[0].strip(),
            total_lec_attended = response.xpath(xpaths['total_lec_attended']).extract()[0].strip(),
            )

def scrape_attendance(USERNAME, PASSWORD, chatID):
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
            deferred = runner.crawl(AttendanceSpider, USERNAME=USERNAME, PASSWORD=PASSWORD, chatID=chatID)
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
