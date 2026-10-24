from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

DB_URL = 'sqlite:///./database.db'
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(engine)
Base = declarative_base()