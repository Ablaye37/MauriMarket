from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    ForeignKey
)

from app.database.database import Base


class OrderItem(Base):

    __tablename__ = "order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    product_title = Column(
        String(200),
        nullable=False
    )

    price = Column(
        Float,
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False,
        default=1
    )

    subtotal = Column(
        Float,
        nullable=False
    )