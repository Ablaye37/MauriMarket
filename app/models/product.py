from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey
)

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
    # INFORMATIONS PRODUIT
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
    # TYPE DE PUBLICATION
    # =====================================================

    publication_type = Column(
        String(50),
        nullable=False,
        default="vente",
        server_default="vente"
    )

    # =====================================================
    # LIVRAISON
    #
    # True  = livraison disponible
    # False = pas de livraison
    # =====================================================

    delivery_available = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
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
    # =====================================================

    category_id = Column(
        Integer,
        ForeignKey(
            "categories.id"
        ),
        nullable=True
    )

    # =====================================================
    # SOUS-CATÉGORIE
    # =====================================================

    subcategory_id = Column(
        Integer,
        ForeignKey(
            "subcategories.id"
        ),
        nullable=True
    )

    # =====================================================
    # PROPRIÉTAIRE
    #
    # IMPORTANT :
    # Le produit appartient à un utilisateur.
    # Lorsqu'un utilisateur est supprimé par l'admin,
    # le code admin supprime d'abord ses produits.
    # =====================================================

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id"
        ),
        nullable=False,
        index=True
    )

    # =====================================================
    # BOUTIQUE
    # =====================================================

    boutique_id = Column(
        Integer,
        ForeignKey(
            "boutiques.id"
        ),
        nullable=True,
        index=True
    )

    # =====================================================
    # STATUT
    # =====================================================

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True
    )

    # =====================================================
    # RELATION CATÉGORIE
    # =====================================================

    category = relationship(
        "Category",
        back_populates="products"
    )

    # =====================================================
    # RELATION SOUS-CATÉGORIE
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