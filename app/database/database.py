import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("SUPABASE_DB_URL")
)

# Si aucune base PostgreSQL n'est configurée,
# utiliser SQLite en local.
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./maurimarket.db"


# ============================================================
# DATABASE INFO
# ============================================================

print("DATABASE CONFIGUREE :", bool(DATABASE_URL))

print(
    "TYPE DATABASE :",
    "SQLITE" if DATABASE_URL.startswith("sqlite") else "POSTGRESQL"
)


# ============================================================
# ENGINE
# ============================================================

if DATABASE_URL.startswith("sqlite"):

    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False
        },
    )

else:

    # PostgreSQL / Supabase / Railway

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=2,
        future=True,
    )


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# BASE
# ============================================================

Base = declarative_base()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()