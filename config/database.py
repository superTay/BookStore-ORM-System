import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv

# 1) Load environment variables from .env
load_dotenv()

# 2) Read sensitive values safely
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "libreria_db")

# 3) Build SQLAlchemy URL (MySQL over PyMySQL)
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# 4) Create engine and Base
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
Base = declarative_base()

# 5) Configure session factory
# Use expire_on_commit=False so ORM instances keep loaded attributes
# after the session commits/closes, which is convenient for CLI/app layers.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

__all__ = ["engine", "Base", "SessionLocal"]
