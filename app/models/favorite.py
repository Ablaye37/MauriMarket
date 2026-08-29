from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Favorite(Base):

    __tablename__ = "favorites"

    # =====================================================
    # IDENTIFIANT
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # UTILISATEUR
    # =====================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =====================================================
    # PRODUIT
    # =====================================================

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =====================================================
    # DATE DE CRÉATION
    # =====================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =====================================================
    # RELATION PRODUIT
    # =====================================================

    product = relationship(
        "Product"
    )

    # =====================================================
    # EMPÊCHER LES DOUBLONS
    # =====================================================

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_favorite_user_product"
        ),
    )