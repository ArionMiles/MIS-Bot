from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from datetime import datetime
from database import Base

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    PID = Column(String(100))
    password = Column(String(50))
    chatID = Column(String(512))
    subjects = relationship('Subject', backref = 'chats')   

    def __init__(self, PID, password, chatID):
        self.PID = PID
        self.password = password
        self.chatID = chatID

    def __repr__(self):
        return '<Chat {} chatID: {}>'.format(self.PID, self.chatID)


class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key = True)
    chat_id = Column(Integer, ForeignKey('Chat.id'))
    name = Column(String(100))  
    attendance = relationship('Attendance', backref = 'subjects')
    
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return '<Subject {} chatID: {}>'.format(self.name, self.chatID)

class Attendance(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key = True)
    subject_id = Column(Integer, ForeignKey('Subject.id'))
    date = Column(DateTime, default=datetime.utcnow)
    value = Column(Integer, default=0)

    def __init__(self, value, date=datetime.utcnow()):
        self.value = value
        self.date = date

    def __repr__(self):
        return '<Attendance {} Date: {} >'.format(self.value, self.date)

    