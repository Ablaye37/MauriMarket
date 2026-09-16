from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class SubCategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)

    # Nom français
    name = Column(
        String(100),
        nullable=False
    )

    # Nom arabe
    name_ar = Column(
        String(100),
        nullable=True
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False
    )

    # Catégorie principale
    category = relationship(
        "Category",
        back_populates="subcategories"
    )

    # Produits de cette sous-catégorie
    products = relationship(
        "Product",
        back_populates="subcategory"
    )