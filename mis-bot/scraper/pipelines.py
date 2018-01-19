# -*- coding: utf-8 -*-

from scraper.database import init_db, db_session
from scraper.models import Attendance

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

class AttendancePipeline(object):
    def process_item(self, item, spider):
        #Initiate DB
        init_db()

        if not Attendance.query.filter(Attendance.chatID == spider.chatID).first():
        	record = Attendance(total_lec_attended=item['total_lec_attended'],
                            total_lec_conducted=item['total_lec_conducted'],
                            chatID=spider.chatID) 
        	db_session.add(record)
        	db_session.commit()
        else:
            db_session.query(Attendance).filter(Attendance.chatID == spider.chatID).\
            update({'total_lec_attended': item['total_lec_attended'],
                    'total_lec_conducted':item['total_lec_conducted']})
            db_session.commit()

        return item
