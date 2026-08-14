import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# =========================
# BASE DE DONNÉES
# =========================

DATABASE_URL = os.environ.get("SUPABASE_DB_URL")


# Supabase/PostgreSQL si la variable existe
# Sinon SQLite local
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )
else:
    DATABASE_URL = "sqlite:///maurimarket.db"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )


# =========================
# SESSION
# =========================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# =========================
# BASE SQLAlchemy
# =========================

Base = declarative_base()


















