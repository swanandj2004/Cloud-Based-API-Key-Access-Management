from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

db = "postgresql+psycopg2://postgres:521452A3s@localhost:5432/projectdb"

engine = create_engine(db)

session = sessionmaker(autoflush=False,bind=engine)