from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Integer, ForeignKey("roles.id"))

class Key(Base):
    __tablename__ = "keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False) 
    created_at = Column(Date,nullable=False)