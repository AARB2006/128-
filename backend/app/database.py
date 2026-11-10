
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Load environment variables from backend/.env
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "ytmp3_beta")

# Construct the MySQL connection URL
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query={"charset": "utf8mb4"}
)

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Used later by FastAPI endpoints
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
