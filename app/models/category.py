from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    # Nom français
    name = Column(String(100), nullable=False)

    # Nom arabe
    name_ar = Column(String(100), nullable=True)

    # Produits de cette catégorie
    products = relationship(
        "Product",
        back_populates="category"
    )

    # Sous-catégories
    subcategories = relationship(
        "SubCategory",
        back_populates="category",
        cascade="all, delete-orphan"
    )