from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base 
from Entities.role import Role

Base = declarative_base 

class Role(Base):
    __table__name="roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

class User(Base):
    __tablename__="users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False) 
    password = Column(String, nullable=False) 
    role = Column(String, ForeignKey("roles.id"))

class Key(Base):
    __tablename__="keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False) 