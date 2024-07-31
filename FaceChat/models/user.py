from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from database import Base
from pgvector.sqlalchemy import Vector

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    contact = Column(String(100), nullable=False)
    face_image = Column(Vector(768))
    voice_sample = Column(Vector(13))
    conversation = Column(String(1000), nullable=False)
    
