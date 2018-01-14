# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class LecturesItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    '''AM = Field()
    AP = Field()
    AC = Field()
    EM = Field()
    BEE = Field()
    EVS = Field()
    Overall = Field()'''
    total_lec_conducted=Field()
    total_lec_attended=Field()

'''class PracticalsItem(Item):
    AC_prac = Field()
    AM_prac = Field()
    AP_prac = Field()
    BEE_prac = Field()
    Workshop = Field()
    EM_prac = Field()
    Overall_prac=Field()
'''