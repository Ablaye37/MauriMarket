from sqlalchemy import Column, Integer, String
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    phone = Column(String(20), unique=True, index=True, nullable=False)

    password = Column(String(255), nullable=False)

