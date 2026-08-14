from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Product(Base):

    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    price = Column(
        Float,
        nullable=False
    )

    city = Column(
        String(100),
        nullable=False
    )

    condition = Column(
        String(50),
        nullable=False
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True
    )

    subcategory_id = Column(
        Integer,
        ForeignKey("subcategories.id"),
        nullable=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    image = Column(
        String(255),
        nullable=True
    )

    category = relationship(
        "Category",
        back_populates="products"
    )

    subcategory = relationship(
        "SubCategory",
        back_populates="products"
    )

    user = relationship(
        "User"
    )