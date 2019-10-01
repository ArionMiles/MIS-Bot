# -*- coding: utf-8 -*-
from os import remove, environ
import logging

from telegram.bot import Bot
from telegram.error import TelegramError
from sqlalchemy import and_

from scraper.database import db_session
from scraper.models import Lecture, Practical, Chat, Misc
from scraper.items import Lectures, Practicals

from misbot.mis_utils import until_x, crop_image

bot = Bot(environ['TOKEN'])

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

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

class AttendanceScreenshotPipeline(object):
    def close_spider(self, spider):
        student_misc = Misc.query.filter(Misc.chatID == spider.chatID).first()
        try:
            bot.send_photo(chat_id=spider.chatID, photo=open("files/{}_attendance.png".format(spider.username), 'rb'),
                       caption='Attendance Report for {}'.format(spider.username))
            if student_misc is not None and student_misc.attendance_target is not None:
                target = student_misc.attendance_target
                no_of_lectures = int(until_x(spider.chatID, target))
                if no_of_lectures > 0:
                    messageContent = "You need to attend {} lectures to meet your target of {}%".format(no_of_lectures, target)
                    bot.sendMessage(chat_id=spider.chatID, text=messageContent)

            remove('files/{}_attendance.png'.format(spider.username)) #Delete saved image
        except IOError:
            bot.sendMessage(chat_id=spider.chatID, text='There were some errors.')
            logger.warning("Attendance screenshot failed! Check if site is blocking us or if Splash is up.")
        except TelegramError as te:
            logger.warning("TelegramError: {}".format(str(te)))

class ItineraryScreenshotPipeline(object):
    def close_spider(self, spider):
        try:
            with open("files/{}_itinerary.png".format(spider.username), "rb") as f:
                pass
        except IOError:
            bot.sendMessage(chat_id=spider.chatID, text='There were some errors.')
            logger.warning("Itinerary screenshot failed! Check if site is blocking us or if Splash is up.")
            return
        except TelegramError as te:
            logger.warning("TelegramError: {}".format(str(te)))
            return

        if spider.uncropped:
            try:
                # arguments supplied, sending full screenshot
                bot.send_document(chat_id=spider.chatID, document=open("files/{}_itinerary.png".format(spider.username), 'rb'),
                                caption='Full Itinerary Report for {}'.format(spider.username))
                remove('files/{}_itinerary.png'.format(spider.username)) #Delete original downloaded image
                return
            except TelegramError as te:
                logger.warning("TelegramError: {}".format(str(te)))

        try:
            if crop_image("files/{}_itinerary.png".format(spider.username)):
                # greater than 800px. cropping and sending..
                bot.send_photo(chat_id=spider.chatID, photo=open("files/{}_itinerary_cropped.png".format(spider.username), 'rb'),
                            caption='Itinerary Report for {}'.format(spider.username))
                remove('files/{}_itinerary_cropped.png'.format(spider.username)) #Delete cropped image
                remove('files/{}_itinerary.png'.format(spider.username)) #Delete original downloaded image
            else:
                # less than 800px, sending as it is..
                bot.send_photo(chat_id=spider.chatID, photo=open("files/{}_itinerary.png".format(spider.username), 'rb'),
                            caption='Itinerary Report for {}'.format(spider.username))
                remove('files/{}_itinerary.png'.format(spider.username)) #Delete original downloaded image
        except TelegramError as te:
            logger.warning("TelegramError: {}".format(str(te)))

class ResultsScreenshotPipeline(object):
    def close_spider(self, spider):
        try:
            bot.send_photo(chat_id=spider.chatID, photo=open("files/{}_tests.png".format(spider.username), 'rb'),
                        caption='Test Report for {}'.format(spider.username))
            remove('files/{}_tests.png'.format(spider.username)) #Delete saved image
        except IOError:
            bot.sendMessage(chat_id=spider.chatID, text='There were some errors.')
            logger.warning("Results screenshot failed! Check if site is blocking us or if Splash is up.")
        except TelegramError as te:
            logger.warning("TelegramError: {}".format(str(te)))

class ProfileScreenshotPipeline(object):
    def close_spider(self, spider):
        try:
            bot.send_document(chat_id=spider.chatID, document=open("files/{}_profile.png".format(spider.username), 'rb'),
                            caption='Student profile for {}'.format(spider.username))
            remove('files/{}_profile.png'.format(spider.username)) #Delete saved image
        except IOError:
            bot.sendMessage(chat_id=spider.chatID, text='There were some errors.')
            logger.warning("Profile screenshot failed! Check if site is blocking us or if Splash is up.")
        except TelegramError as te:
            logger.warning("TelegramError: {}".format(str(te)))
