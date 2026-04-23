from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
logger.debug(f"DATABASE_URL chargé : {DATABASE_URL}")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL manquant dans le fichier .env")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()