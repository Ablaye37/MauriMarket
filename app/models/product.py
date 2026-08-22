from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Product(Base):
    __tablename__ = "products"

    # =====================================================
    # IDENTIFIANT
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # INFORMATIONS DU PRODUIT
    # =====================================================

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    price = Column(
        Float,
        nullable=False
    )

    city = Column(
        String(100),
        nullable=True
    )

    condition = Column(
        String(50),
        nullable=True
    )

    # =====================================================
    # IMAGE
    # =====================================================

    image = Column(
        String(500),
        nullable=True
    )

    # =====================================================
    # CATÉGORIE
    #
    # IMPORTANT :
    # Cette partie est laissée telle quelle.
    # On ne travaille pas sur les catégories actuellement.
    # =====================================================

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True
    )

    # =====================================================
    # SOUS-CATÉGORIE
    #
    # IMPORTANT :
    # Cette partie est laissée telle quelle.
    # =====================================================

    subcategory_id = Column(
        Integer,
        ForeignKey("subcategories.id"),
        nullable=True
    )

    # =====================================================
    # PROPRIÉTAIRE DU PRODUIT
    # =====================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # =====================================================
    # BOUTIQUE
    #
    # NULL = produit normal
    # ID   = produit appartenant à une boutique
    #
    # C'est cette relation qui permet de faire :
    #
    # Ma boutique
    #      ↓
    # produit
    #      ↓
    # boutique_id
    #      ↓
    # boutique
    #
    # Le même produit peut alors être affiché :
    # - dans Ma boutique
    # - dans la page publique de la boutique
    # - sur l'accueil comme produit provenant d'une boutique
    # =====================================================

    boutique_id = Column(
        Integer,
        ForeignKey("boutiques.id"),
        nullable=True,
        index=True
    )

    # =====================================================
    # RELATION CATÉGORIE
    #
    # Conservée sans modification de logique.
    # =====================================================

    category = relationship(
        "Category",
        back_populates="products"
    )

    # =====================================================
    # RELATION SOUS-CATÉGORIE
    #
    # Conservée sans modification de logique.
    # =====================================================

    subcategory = relationship(
        "SubCategory",
        back_populates="products"
    )

    # =====================================================
    # RELATION UTILISATEUR
    # =====================================================

    user = relationship(
        "User",
        back_populates="products"
    )

    # =====================================================
    # RELATION BOUTIQUE
    # =====================================================

    boutique = relationship(
        "Boutique",
        back_populates="products"
    )