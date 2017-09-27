import os
from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from ..items import LecturesItem, PracticalsItem
from scrapy.shell import inspect_response
from scrapy.crawler import CrawlerProcess

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

xpath = {
    #Lectures
    'AM_pcent': '//table[1]/tr[3]/td[4]/text()',
    'AM_pcent_red' : '//table[1]/tr[3]/td[4]/font/u/b/text()',
    'AP_pcent': '//table[1]/tr[4]/td[4]/text()',
    'AP_pcent_red' : '//table[1]/tr[4]/td[4]/font/u/b/text()',
    'AC_pcent' : '//table[1]/tr[5]/td[4]/text()',
    'AC_pcent_red': '//table[1]/tr[5]/td[4]/font/u/b/text()',
    'EM_pcent' : '//table[1]/tr[6]/td[4]/text()',
    'EM_pcent_red': '//table[1]/tr[6]/td[4]/font/u/b/text()',
    'BEE_pcent' : '//table[1]/tr[7]/td[4]/text()',
    'BEE_pcent_red': '//table[1]/tr[7]/td[4]/font/u/b/text()',
    'EVS_pcent' : '//table[1]/tr[8]/td[4]/text()',
    'EVS_pcent_red': '//table[1]/tr[8]/td[4]/font/u/b/text()',
    'Overall' : '//center/h2/text()',
    'Overall_red': '//center/h2/u/b/text()',
    'total_lec_conducted' : '//table[1]/tr[9]/td[2]/b/text()',
    'total_lec_attended' : '//table[1]/tr[9]/td[3]/b/text()',
    #Practicals
    'AC_prac': '//table[2]/tr[2]/td[4]/text()',
    'AC_prac_red' : '//table[2]/tr[2]/td[4]/font/u/b/text()',
    'AM_prac' : '//table[2]/tr[3]/td[4]/text()',
    'AM_prac_red': '//table[2]/tr[3]/td[4]/font/u/b/text()',
    'BEE_prac': '//table[2]/tr[4]/td[4]/text()',
    'BEE_prac_red': '//table[2]/tr[4]/td[4]/font/u/b/text()',
    'Workshop': '//table[2]/tr[5]/td[4]/text()',
    'Workshop_red': '//table[2]/tr[5]/td[4]/font/u/b/text()',
    'EM_prac' : '//table[2]/tr[6]/td[4]/text()',
    'EM_prac_red' : '//table[2]/tr[6]/td[4]/font/u/b/text()',
    'Overall_prac': '//label/h2/text()',
    'Overall_prac_red' : '//label/h2/b/text()'
}

class MySpider(InitSpider):
    name = 'mis'
    allowed_domains = ['report.aldel.org']
    login_page = 'http://report.aldel.org/student_page.php'
    start_urls = ['http://report.aldel.org/student/attendance_report.php']


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
        if USERNAME in response.body:
            self.log("Login Successful!")
            # Now the crawling can begin..
            return self.initialized()
        else:
            self.log("Login failed! Check site status and credentials.")
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        '''Scrape attendance data from page'''
        #inspect_response(response, self) #for debugging

        #LECTURES
        if response.xpath(xpath['AM_pcent']).extract()[0].strip() == "":
            AM = response.xpath(xpath['AM_pcent_red']).extract()[0].strip()
        else:
            AM = response.xpath(xpath['AM_pcent']).extract()[0].strip()
        
        if response.xpath(xpath['AP_pcent']).extract()[0].strip() == "":
            AP = response.xpath(xpath['AP_pcent_red']).extract()[0].strip()
        else:
            AP = response.xpath(xpath['AP_pcent']).extract()[0].strip()
        
        if response.xpath(xpath['AC_pcent']).extract()[0].strip() == "":
            AC = response.xpath(xpath['AC_pcent_red']).extract()[0].strip()
        else:
            AC = response.xpath(xpath['AC_pcent']).extract()[0].strip()
        
        if response.xpath(xpath['EM_pcent']).extract()[0].strip() == "":
            EM = response.xpath(xpath['EM_pcent_red']).extract()[0].strip()
        else:
            EM = response.xpath(xpath['EM_pcent']).extract()[0].strip()
        
        if response.xpath(xpath['BEE_pcent']).extract()[0].strip() == "":
            BEE = response.xpath(xpath['BEE_pcent_red']).extract()[0].strip()
        else:
            BEE = response.xpath(xpath['BEE_pcent']).extract()[0].strip()
        
        if response.xpath(xpath['EVS_pcent']).extract()[0].strip() == "":
            EVS = response.xpath(xpath['EVS_pcent_red']).extract()[0].strip()
        else:
            EVS = response.xpath(xpath['EVS_pcent']).extract()[0].strip()
        
        if response.xpath(xpath['Overall']).extract()[0].strip() == "Overall Attendance:":
            Overall = response.xpath(xpath['Overall_red']).extract()[0].strip()
        else:
            Overall = response.xpath(xpath['Overall']).extract()[0].strip()
        
        #PRACTICALS
        if response.xpath(xpath['AC_prac']).extract()[0].strip() == "":
            AC_prac = response.xpath(xpath['AC_prac_red']).extract()[0].strip()
        else:
            AC_prac = response.xpath(xpath['AC_prac']).extract()[0].strip()
        
        if response.xpath(xpath['AM_prac']).extract()[0].strip() == "":
            AM_prac = response.xpath(xpath['AM_prac_red']).extract()[0].strip()
        else:
            AM_prac = response.xpath(xpath['AM_prac']).extract()[0].strip()
        
        if response.xpath(xpath['BEE_prac']).extract()[0].strip() == "":
            BEE_prac = response.xpath(xpath['BEE_prac_red']).extract()[0].strip()
        else:
            BEE_prac = response.xpath(xpath['BEE_prac']).extract()[0].strip()
        
        if response.xpath(xpath['Workshop']).extract()[0].strip() == "":
            Workshop = response.xpath(xpath['Workshop_red']).extract()[0].strip()
        else:
            Workshop = response.xpath(xpath['Workshop']).extract()[0].strip()
        
        if response.xpath(xpath['EM_prac']).extract()[0].strip() == "":
            EM_prac = response.xpath(xpath['EM_prac_red']).extract()[0].strip()
        else:
            EM_prac = response.xpath(xpath['EM_prac']).extract()[0].strip()
        
        if response.xpath(xpath['Overall_prac']).extract()[0].strip() == "Overall Practical Attendance:":
            Overall_prac = response.xpath(xpath['Overall_prac_red']).extract()[0].strip()
        else:
            Overall_prac = str(response.xpath(xpath['Overall_prac']).extract()).strip()[33:]
        
        

        yield LecturesItem(
            AM=AM,
            AP=AP,
            AC=AC,
            EM=EM,
            BEE=BEE,
            EVS=EVS,
            Overall=Overall,
            total_lec_conducted=response.xpath(xpath['total_lec_conducted']).extract()[0].strip(),
            total_lec_attended=response.xpath(xpath['total_lec_attended']).extract()[0].strip()
        )

        yield PracticalsItem(
            AC_prac=AC_prac,
            AM_prac=AM_prac,
            BEE_prac=BEE_prac,
            Workshop=Workshop,
            EM_prac=EM_prac,
            Overall_prac=Overall_prac,
        )