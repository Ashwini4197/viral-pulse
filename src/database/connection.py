"""
viral_pulse/src/database/connection.py
PostgreSQL connection pool using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """Create and return a SQLAlchemy engine using env variables."""
    db_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
    )
    return create_engine(db_url, pool_size=5, max_overflow=10)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection():
    """Quick health check — prints PostgreSQL version."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("✅ DB connected:", result.scalar())


if __name__ == "__main__":
    test_connection()
