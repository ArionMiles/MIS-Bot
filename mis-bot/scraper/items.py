# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class LecturesItem(Item):
    total_lec_conducted=Field()
    total_lec_attended=Field()
