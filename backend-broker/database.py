import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use Supabase PostgreSQL by default, fallback to SQLite for development
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:iVYlzK02219DCVcF@db.mzyurrvepchpkzmbzqyx.supabase.co:5432/postgres')

# For local development without Supabase, uncomment the line below:
# DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./frankie.db')

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() 