from os import environ
import base64
from multiprocessing import Process, Queue

from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from scrapy_splash import SplashRequest
import scrapy.crawler as crawler
from twisted.internet import reactor

from misbot.mis_utils import solve_captcha

class ResultsSpider(InitSpider):
    """Take screenshot of ``http://report.aldel.org/student/test_marks_report.php``
    and send it to the user via :py:class:`scraper.pipelines.ResultsScreenshotPipeline`
    
    :param InitSpider: Base Spider with initialization facilities
    :type InitSpider: Spider
    """
    name = 'results'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/student_page.php'
    start_urls = ['http://report.aldel.org/student/test_marks_report.php']

    def __init__(self, username, password, chatID, *args, **kwargs):
        super(ResultsSpider, self).__init__(*args, **kwargs)
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
        url = 'http://report.aldel.org/student/test_marks_report.php'
        splash_args = {
            'html': 1,
            'png': 1,
            'wait':0.1,
            'render_all':1
        }
        self.logger.info("Taking snapshot of Test Report for {}...".format(self.username))
        yield SplashRequest(url, self.parse_result, endpoint='render.json', args=splash_args)

    def parse_result(self, response):
        """Downloads and saves the attendance report in ``files/<Student_ID>_tests.png``
        format.
        """
        imgdata = base64.b64decode(response.data['png'])
        filename = 'files/{}_tests.png'.format(self.username)
        with open(filename, 'wb') as f:
            f.write(imgdata)
            self.logger.info("Saved test report as: {}_tests.png".format(self.username))

def scrape_results(username, password, chatID):
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
                'ITEM_PIPELINES': {'scraper.pipelines.ResultsScreenshotPipeline':300,},

                'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                           'scrapy_splash.SplashMiddleware': 725,
                                           'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,},

                'SPLASH_URL':environ['SPLASH_INSTANCE'],
                'SPIDER_MIDDLEWARES':{'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
                'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
                'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            })
            deferred = runner.crawl(ResultsSpider, username=username, password=password, chatID=chatID)
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
