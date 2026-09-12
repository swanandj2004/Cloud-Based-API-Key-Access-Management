from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base 
from Entities.role import Role

Base = declarative_base 

class User(Base):
    __tablename__="users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False) 
    password = Column(String, nullable=False) 
    role = Column(Role, nullable=False)

class Role(Base):
    __table__name="roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class Key(Base):
    __tablename__="keys"
    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False) 