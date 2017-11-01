from sqlalchemy import Column, Integer, String
from database import Base

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