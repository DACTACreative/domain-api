from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://domain_api_db_user:1mvna6F3NRpaKVQ5C7Q5gO2TY291aRjm@dpg-d0ht7pumcj7s739g7gc0-a.oregon-postgres.render.com/domain_api_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
