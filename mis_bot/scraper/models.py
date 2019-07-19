import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy_utils.types.choice import ChoiceType

from scraper.database import Base

class Lecture(Base):
    __tablename__ = 'lectures'
    id = Column(Integer, primary_key=True)
    chatID = Column(Integer)
    name = Column(String(100))
    attended = Column(Integer, default=0)
    conducted = Column(Integer, default=0)

    def __init__(self, name, chatID, conducted, attended):
        self.name = name
        self.chatID = chatID
        self.conducted = conducted
        self.attended = attended

    def __repr__(self):
        return '<Lectures {} Conducted {} Attended {} chatID: {}>'.format(self.name, self.conducted, self.attended, self.chatID)

class Practical(Base):
    __tablename__ = 'practicals'
    id = Column(Integer, primary_key=True)
    chatID = Column(Integer)
    name = Column(String(100))
    attended = Column(Integer, default=0)
    conducted = Column(Integer, default=0)

    def __init__(self, name, chatID, conducted, attended):
        self.name = name
        self.chatID = chatID
        self.conducted = conducted
        self.attended = attended

    def __repr__(self):
        return '<Practicals: {} Conducted {} Attended {} chatID: {}>'.format(self.name, self.conducted, self.attended, self.chatID)


class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    PID = Column(String(100))
    password = Column(String(50))
    DOB = Column(String(100))
    chatID = Column(String(512))  

    def __init__(self, PID=None, password=None, DOB=None, chatID=None):
        self.PID = PID
        self.password = password
        self.DOB = DOB
        self.chatID = chatID

    def __repr__(self):
        return '<Chat {} chatID: {}>'.format(self.PID, self.chatID)

class Misc(Base):
    __tablename__ = 'misc'
    id = Column(Integer, primary_key=True)
    chatID = Column(String(512))
    attendance_target = Column(Float)

    def __init__(self, chatID=chatID, attendance_target=None):
        self.chatID = chatID
        self.attendance_target = attendance_target
    
    def __repr(self):
        return '<Misc chatID: {}>'.format(self.chatId)


def generate_uuid():
    return str(uuid.uuid4())

class PushMessage(Base):
    __tablename__ = 'pushmessages'
    uuid = Column(String(512), primary_key=True, default=generate_uuid)
    text = Column(String(4096))
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __init__(self, text=text, created_at=None):
        self.text = text
        self.created_at = created_at

    def __repr__(self):
        return '<{} | {}>'.format(self.uuid, self.text)

class PushNotification(Base):
    __tablename__ = 'pushnotifications'
    id = Column(Integer, primary_key=True)
    message_uuid = Column(String(512))
    chatID = Column(String(512))
    message_id = Column(Integer, default=0)
    sent = Column(Boolean, default=False)
    failure_reason = Column(String(512))

    def __init__(self, message_uuid=message_uuid, chatID=chatID, message_id=message_id, sent=sent, failure_reason=None):
        self.message_uuid = message_uuid
        self.chatID = chatID
        self.message_id = message_id
        self.sent = sent
        self.failure_reason = failure_reason

    def __repr__(self):
        return '<Push Notification {} | {}>'.format(self.chatID, self.message_id)

class RateLimit(Base):
    STAGES = [
        ('new', 'New'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
    ]

    COMMANDS = [
        ('attendance', 'Attendance'),
        ('itinerary', 'Itinerary'),
        ('results', 'Results'),
        ('profile', 'Profile'),
    ]

    __tablename__ = 'ratelimit'
    id = Column(Integer, primary_key=True)
    chatID = Column(String(512))
    requested_at = Column(DateTime, default=datetime.now)
    status = Column(ChoiceType(STAGES))
    command = Column(ChoiceType(COMMANDS))
    count = Column(Integer)

    def __init__(self, chatID, status, command, count, requested_at=None):
        self.chatID = chatID
        self.requested_at = requested_at
        self.status = status
        self.command = command
        self.count = count
    
    def __repr__(self):
        return '<Rate Limit {} | {}>'.format(self.chatID, self.command)
