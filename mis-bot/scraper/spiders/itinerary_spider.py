#!/usr/local/bin/python3
from os import environ
import base64
from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
import scrapy.crawler as crawler
from twisted.internet import reactor
from multiprocessing import Process, Queue
from scrapy_splash import SplashRequest

from ..items import Lectures, Practicals
from ..captcha import captcha_solver

class ItinerarySpider(InitSpider):
    name = 'itinerary'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/parent_page.php'
    start_urls = ['http://report.aldel.org/parent/itinenary_attendance_report.php']

    def __init__(self, USERNAME, DOB, *args, **kwargs):
        super(ItinerarySpider, self).__init__(*args, **kwargs)
        self.USERNAME = USERNAME
        self.DOB = DOB
   
    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        try:
            date, month, year = self.DOB.split('/')
        except ValueError:
            self.logger.warning("Incorrect DOB details. Terminating operation.")

        sessionID = str(response.headers.getlist('Set-Cookie')[0].decode().split(';')[0].split("=")[1])
        captcha_answer = captcha_solver(sessionID)
        self.logger.info("Captcha Answer: %s" % (captcha_answer))
        return FormRequest.from_response(response, formdata={'studentid': self.USERNAME,
                                                             'date_of_birth': date,
                                                             'month_of_birth': month,
                                                             'year_of_birth': year,
                                                             'captcha_code':captcha_answer},
                                         callback=self.check_login_response)

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in."""
        if self.USERNAME in response.body.decode():
            self.logger.info("Login Successful!")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.logger.warning("Login failed! Check site status and credentials.")
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        url = 'http://report.aldel.org/parent/itinenary_attendance_report.php'
        splash_args = {
            'html': 1,
            'png': 1,
            'wait':0.1,
            'render_all':1
        }
        self.logger.info("Taking snapshot of Itinerary Attendance Report for {}...".format(self.USERNAME))
        yield SplashRequest(url, self.parse_result, endpoint='render.json', args=splash_args)

    def parse_result(self, response):
        '''Store the screenshot'''
        imgdata = base64.b64decode(response.data['png'])
        filename = 'files/{}_itinerary.png'.format(self.USERNAME)
        with open(filename, 'wb') as f:
            f.write(imgdata)
            self.logger.info("Saved itinerary attendance report as: {}_itinerary.png".format(self.USERNAME))


def scrape_itinerary(USERNAME, DOB):
    '''Run the spider multiple times, without hitting ReactorNotRestartable.Forks own process.'''
    def f(q):
        try:
            runner = crawler.CrawlerRunner({
                'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                           'scrapy_splash.SplashMiddleware': 725,
                                           'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,},

                'SPLASH_URL':environ['SPLASH_INSTANCE'],
                'SPIDER_MIDDLEWARES':{'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
                'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
            })
            deferred = runner.crawl(ItinerarySpider, USERNAME=USERNAME, DOB=DOB, chatID=chatID)
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
