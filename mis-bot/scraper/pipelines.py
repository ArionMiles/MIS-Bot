# -*- coding: utf-8 -*-

from scraper.database import init_db, db_session
from scraper.models import Lecture, Practical, Chat
from sqlalchemy import and_

from scraper.items import Lectures, Practicals

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

class LecturePipeline(object):
    def process_item(self, item, spider):
        if not isinstance(item, Lectures):
            return item #Do nothing for Practical Items (NOT Lectures)

        if not Lecture.query.filter(and_(Lecture.chatID == spider.chatID, Lecture.name == item['subject'])).first():
            record = Lecture(name=item['subject'],
                            chatID=spider.chatID,
                            attended=item['attended'],
                            conducted=item['conducted'])
            db_session.add(record)
            db_session.commit()

        else:
            db_session.query(Lecture).filter(and_(Lecture.chatID == spider.chatID, Lecture.name == item['subject'])).\
            update({'attended': item['attended'],
                    'conducted':item['conducted']})
            db_session.commit()
        return item

class PracticalPipeline(object):
    def process_item(self, item, spider):
        if not isinstance(item, Practicals):
            return item #Do nothing for Lectures Items (NOT Practicals)

        if not Practical.query.filter(and_(Practical.chatID == spider.chatID, Practical.name == item['subject'])).first():
            record = Practical(name=item['subject'],
                            chatID=spider.chatID,
                            attended=item['attended'],
                            conducted=item['conducted'])
            db_session.add(record)
            db_session.commit()

        else:
            db_session.query(Practical).filter(and_(Practical.chatID == spider.chatID, Practical.name == item['subject'])).\
            update({'attended': item['attended'],
                    'conducted':item['conducted']})
            db_session.commit()
        return item