from sqlalchemy import Column, Integer, String
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
    chatID = Column(String(512))  

    def __init__(self, PID, password, chatID):
        self.PID = PID
        self.password = password
        self.chatID = chatID

    def __repr__(self):
        return '<Chat {} chatID: {}>'.format(self.PID, self.chatID)