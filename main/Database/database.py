from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

db = os.environ["DATABASE_URL"]
engine = create_engine(db)

session = sessionmaker(autoflush=False,bind=engine)