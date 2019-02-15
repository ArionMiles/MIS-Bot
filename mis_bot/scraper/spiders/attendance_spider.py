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

class AttendanceSpider(InitSpider):
    """Scrape attendance figures from ``http://report.aldel.org/student/attendance_report.php``
    and store the figures in database with :py:class:`scraper.pipelines.LecturePipeline`
    and :py:class:`scraper.pipelines.PracticalPipeline`
    
    :param InitSpider: Base Spider with initialization facilities
    :type InitSpider: Spider
    """

    name = 'attendance'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/student_page.php'
    start_urls = ['http://report.aldel.org/student/attendance_report.php']

    def __init__(self, username, password, chatID, *args, **kwargs):
       super(AttendanceSpider, self).__init__(*args, **kwargs)
       self.username = username
       self.password = password
       self.chatID = chatID
    
    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        session_id = str(response.headers.getlist('Set-Cookie')[0].decode().split(';')[0].split("=")[1])
        captcha_answer = solve_captcha(session_id)
        self.logger.info("Captcha Answer: {}".format(captcha_answer))
        return FormRequest.from_response(response,
                    formdata={'studentid': self.username, 'studentpwd': self.password, 'captcha_code':captcha_answer},
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

        url = 'http://report.aldel.org/student/attendance_report.php'
        splash_args = {
            'html': 1,
            'png': 1,
            'wait':0.1,
            'render_all':1
        }
        self.logger.info("Taking snapshot of Attendance Report for {}...".format(self.username))
        yield SplashRequest(url, self.parse_result, endpoint='render.json', args=splash_args)

    def parse_result(self, response):
        """Downloads and saves the attendance report in ``files/<Student_ID>_attendance.png``
        format.

        Also scrapes every attendance record from the webpage and passes it to
        ``LecturePipeline`` and ``PracticalPipeline``.
        """
        imgdata = base64.b64decode(response.data['png'])
        filename = 'files/{}_attendance.png'.format(self.username)
        with open(filename, 'wb') as f:
            f.write(imgdata)
            self.logger.info("Saved attendance report as: {}_attendance.png".format(self.username))
        
        """CODE FOR SCRAPING EVERY ELEMENT FROM THE TABLE"""
        lecturesItems = response.xpath('//table[1]/tbody/tr')
        for item in lecturesItems[2:]: # starting from 2nd element since 1st row is Student Name
            lec_item = Lectures()
            
            lec_item['subject'] = "".join([x.strip('\n').strip(' ') for x in item.xpath('.//td[1]//text()').extract()])
            lec_item['conducted'] = "".join([x.strip('\n').strip(' ') for x in item.xpath('.//td[2]//text()').extract()])
            lec_item['attended'] = "".join([x.strip('\n').strip(' ') for x in item.xpath('.//td[3]//text()').extract()])
            yield lec_item

        practicalsItems = response.xpath('//table[2]/tbody/tr')
        for item in practicalsItems[1:]:
            prac_item = Practicals()

            prac_item['subject'] = "".join([x.strip('\n').strip(' ') for x in item.xpath('.//td[1]//text()').extract()])
            prac_item['conducted'] = "".join([x.strip('\n').strip(' ') for x in item.xpath('.//td[2]//text()').extract()])
            prac_item['attended'] = "".join([x.strip('\n').strip(' ') for x in item.xpath('.//td[3]//text()').extract()])
            yield prac_item

def scrape_attendance(username, password, chatID):
    """Run the spider multiple times, without hitting ``ReactorNotRestartable`` exception. Forks own process.
    
    :param username: student's PID (format: XXXNameXXXX)
                     where   X - integers
    :type username: str
    :param password: student's password for student portal
    :type password: str
    :param chatID: 9-Digit unique user ID
    :type chatID: str
    """
    def f(q):
        try:
            runner = crawler.CrawlerRunner({
                'ITEM_PIPELINES': {'scraper.pipelines.LecturePipeline': 300,
                                   'scraper.pipelines.PracticalPipeline': 400,
                                   'scraper.pipelines.AttendanceScreenshotPipeline':500,},

                'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                           'scrapy_splash.SplashMiddleware': 725,
                                           'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,},

                'SPLASH_URL':environ['SPLASH_INSTANCE'],
                'SPIDER_MIDDLEWARES':{'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
                'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
            })
            deferred = runner.crawl(AttendanceSpider, username=username, password=password, chatID=chatID)
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
