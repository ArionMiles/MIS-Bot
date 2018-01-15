from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
#from datetime import datetime
from database import Base

"""
Chat --> Subject --> Attendance
One      Many        Many

- Making New Chats
    c = Chat(PID, password, chatId)

- Adding subject to a chat object 'c'
    s = Subject(SubjName)
    c.subjects.append(s)
    db_session.commit()

- Adding an attendance to subject 's' of chat 'c'
    a = Attendance(Value, date=datetime.datetime.utcnow())
    s = c.subjects.query.filter_by(name=SubjName)
    s.attendances.append(a)
    db_session.commit()

"""

class Attendance(Base):
    __tablename__ = 'attendances'
    id = Column(Integer, primary_key = True)
    total_lec_attended = Column(Integer, default=0)
    total_lec_conducted = Column(Integer, default=0)
    #date = Column(DateTime, default=datetime.utcnow)
    #value = Column(Integer, default=0)

    def __init__(self, id=None, total_lec_attended=0, total_lec_conducted=0):
        self.id = id
        self.total_lec_attended = total_lec_attended
        self.total_lec_conducted = total_lec_conducted

    def __repr__(self):
        return '<Attendance Data: {} total_lec_attended: {} total_lec_conducted: {}>'.format(self.id, self.total_lec_attended, self.total_lec_conducted)

'''class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key = True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    name = Column(String(100))  
    attendances = relationship('Attendance', backref = 'subjects')
    
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return '<Subject {} chatID: {}>'.format(self.name, self.chat_id)    
'''
class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    PID = Column(String(100))
    password = Column(String(50))
    chatID = Column(String(512))
    #subjects = relationship('Subject', backref = 'chats')   

    def __init__(self, PID, password, chatID):
        self.PID = PID
        self.password = password
        self.chatID = chatID

    def __repr__(self):
        return '<Chat {} chatID: {}>'.format(self.PID, self.chatID)
