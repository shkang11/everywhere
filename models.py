from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey

# 테이블 정의
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(200))
    hashed_password = Column(String(512))

class Free(Base):
    __tablename__ = 'free'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    username = Column(String(100), ForeignKey('users.username'))
    title = Column(String(100))
    content = Column(String(1000))

class Question(Base):
    __tablename__ = 'question'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    username = Column(String(100), ForeignKey('users.username'))
    title = Column(String(100))
    content = Column(String(1000))

class Share(Base):
    __tablename__ = 'share'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    username = Column(String(100), ForeignKey('users.username'))
    title = Column(String(100))
    content = Column(String(1000))