# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import codecs
#import scrapy
'''
class MisPipeline(object):
    def __init__(self):
        self.file = open("output.json", 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()
 
    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()
 
    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
'''
class MisPipeline(object):
    def open_spider(self, spider):
        self.file = open('../attendance_report.json', 'wb')
        self.file.write("[")

    def close_spider(self, spider):
        self.file.write("]")
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(
            dict(item),
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        ) + "\n"

        self.file.write(line)
        return item
    '''def __init__(self):
        self.file = codecs.open('../data_utf8.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        self.file.write(json.dumps([{'lectures': dict(item)}], indent=4))
        return item

    def close_spider(self, spider):
        self.file.close()
'''