# -*- coding: utf-8 -*-

from ..database import init_db, db_session
from ..models import Attendance

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

class AttendancePipeline(object):
    def process_item(self, item, spider):
        #Initiate DB
        init_db()
        # create a new SQL Alchemy object and add to the db session
        record = Attendance(total_lec_attended=item['total_lec_attended'],
                            total_lec_conducted=item['total_lec_conducted'])
        db_session.add(record)
        db_session.commit()
        return item
