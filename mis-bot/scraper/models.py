from sqlalchemy import Column, Integer, String, Float
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