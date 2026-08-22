from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey
)

from app.database.database import Base


class Order(Base):

    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    customer_name = Column(
        String(100),
        nullable=False
    )

    customer_phone = Column(
        String(30),
        nullable=False
    )

    city = Column(
        String(100),
        nullable=False
    )

    delivery_address = Column(
        String(255),
        nullable=True
    )

    comment = Column(
        Text,
        nullable=True
    )

    total = Column(
        Float,
        nullable=False,
        default=0
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending"
    )

    payment_status = Column(
        String(30),
        nullable=False,
        default="pending"
    )

    payment_method = Column(
        String(30),
        nullable=False,
        default="manuel"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )