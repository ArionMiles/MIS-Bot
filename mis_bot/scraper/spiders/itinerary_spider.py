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
from misbot.mis_utils import solve_captcha

class ItinerarySpider(InitSpider):
    """Take screenshot of ``http://report.aldel.org/parent/itinenary_attendance_report.php``
    and send it to the user via :py:class:`scraper.pipelines.ItineraryScreenshotPipeline`
    
    :param InitSpider: Base Spider with initialization facilities
    :type InitSpider: Spider
    """
    name = 'itinerary'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/parent_page.php'
    start_urls = ['http://report.aldel.org/parent/itinenary_attendance_report.php']

    def __init__(self, username, dob, chatID, uncropped=False, *args, **kwargs):
        super(ItinerarySpider, self).__init__(*args, **kwargs)
        self.username = username
        self.dob = dob
        self.chatID = chatID
        self.uncropped = uncropped
   
    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        try:
            date, month, year = self.dob.split('/')
        except ValueError:
            self.logger.warning("Incorrect dob details. Terminating operation.")

        session_id = str(response.headers.getlist('Set-Cookie')[0].decode().split(';')[0].split("=")[1])
        captcha_answer = solve_captcha(session_id)
        self.logger.info("Captcha Answer: {}".format(captcha_answer))
        return FormRequest.from_response(response, formdata={'studentid': self.username,
                                                             'date_of_birth': date,
                                                             'month_of_birth': month,
                                                             'year_of_birth': year,
                                                             'captcha_code':captcha_answer},
                                         callback=self.check_login_response)

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in."""
        if self.username in response.body.decode():
            self.logger.info("Login Successful!")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.logger.warning("Login failed! Check site status and credentials.")
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        """Send a SplashRequest and forward the response to :py:func:`parse_result`"""
        url = 'http://report.aldel.org/parent/itinenary_attendance_report.php'
        splash_args = {
            'html': 1,
            'png': 1,
            'wait':0.1,
            'render_all':1
        }
        self.logger.info("Taking snapshot of Itinerary Attendance Report for {}...".format(self.username))
        yield SplashRequest(url, self.parse_result, endpoint='render.json', args=splash_args)

    def parse_result(self, response):
        """Downloads and saves the attendance report in ``files/<Student_ID>_itinerary.png``
        format.
        """
        imgdata = base64.b64decode(response.data['png'])
        filename = 'files/{}_itinerary.png'.format(self.username)
        with open(filename, 'wb') as f:
            f.write(imgdata)
            self.logger.info("Saved itinerary attendance report as: {}_itinerary.png".format(self.username))
            self.logger.info(response.request.headers['User-Agent'])


def scrape_itinerary(username, dob, chatID, uncropped=False):
    """Run the spider multiple times, without hitting ``ReactorNotRestartable`` exception. Forks own process.
    
    :param username: student's PID (format: XXXNameXXXX)
                     where   X - integers
    :type username: str
    :param dob: User's Date of Birth
    :type dob: str
    :param chatID: 9-Digit unique user ID
    :type chatID: str
    :param uncropped: Whether the user wants full report or for last 7-8 days
    :type uncropped: bool
    """
    def f(q):
        try:
            runner = crawler.CrawlerRunner({
                'ITEM_PIPELINES': {'scraper.pipelines.ItineraryScreenshotPipeline':300,},

                'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                           'scrapy_splash.SplashMiddleware': 725,
                                           'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,},

                'SPLASH_URL':environ['SPLASH_INSTANCE'],
                'SPIDER_MIDDLEWARES':{'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
                'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
                'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            })
            deferred = runner.crawl(ItinerarySpider, username=username, dob=dob, chatID=chatID, uncropped=uncropped)
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
