from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from scraper.database import Base


class Attendance(Base):
    __tablename__ = 'attendances'
    id = Column(Integer, primary_key = True)
    total_lec_attended = Column(Integer, default=0)
    total_lec_conducted = Column(Integer, default=0)
    chatID = Column(String(512))

    def __init__(self, chatID, total_lec_attended=0, total_lec_conducted=0):
        self.total_lec_attended = total_lec_attended
        self.total_lec_conducted = total_lec_conducted
        self.chatID = chatID

    def __repr__(self):
        return '<attended: {} || conducted: {} || chatID: {}>'.format(self.total_lec_attended, \
            self.total_lec_conducted, self.chatID)

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
        return '<PID: {} || chatID: {}>'.format(self.PID, self.chatID)
