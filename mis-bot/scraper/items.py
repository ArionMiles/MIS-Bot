# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field

class Lectures(Item):
    subject = Field()
    conducted = Field()
    attended = Field()

class Practicals(Item):
    subject = Field()
    conducted = Field()
    attended = Field()
