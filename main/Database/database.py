from sqlalchemy.orm import sessionmaker 
from sqlalchemy import create_engine

db = "postgresql//:postgres:521452A3s@localhost:5432/projectdb"
engine = create_engine(db)
session = sessionmaker(autoflush=False, bind=engine) 