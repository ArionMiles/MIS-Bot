import base64
from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from scrapy_splash import SplashRequest

class ResultsSpider(InitSpider):
    name = 'results'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/student_page.php'
    start_urls = ['http://report.aldel.org/student/test_marks_report.php']

    def __init__(self, USERNAME, PASSWORD, *args, **kwargs):
        super(ResultsSpider, self).__init__(*args, **kwargs)
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
        if self.USERNAME in response.body:
            self.log("Login Successful!")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.log("Login failed! Check site status and credentials.")
            # Something went wrong, we couldn't log in, so nothing happens.
    def parse(self, response):
        '''Start SplashRequest'''
        url = 'http://report.aldel.org/student/test_marks_report.php'
        splash_args = {
            'html': 1,
            'png': 1
        }
        yield SplashRequest(url, self.parse_result, endpoint='render.json', args=splash_args)

    def parse_result(self, response):
        '''Store the screenshot'''
        imgdata = base64.b64decode(response.data['png'])
        filename = '{}.png'.format(self.USERNAME)
        with open(filename, 'wb') as f:
            f.write(imgdata)
