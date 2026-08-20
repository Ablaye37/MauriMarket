from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Boutique(Base):

    __tablename__ = "boutiques"

    # =====================================================
    # IDENTIFIANT
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # INFORMATIONS PRINCIPALES
    # =====================================================

    name = Column(
        String(150),
        nullable=False
    )

    sale_type = Column(
        String(100),
        nullable=False
    )

    # =====================================================
    # PROFIL DE LA BOUTIQUE
    # =====================================================

    description = Column(
        Text,
        nullable=True
    )

    city = Column(
        String(100),
        nullable=True
    )

    logo = Column(
        String(500),
        nullable=True
    )
    cover_image = Column(
    String(500),
    nullable=True
)

    # =====================================================
    # PROPRIÉTAIRE
    # =====================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="boutique"
    )

    # =====================================================
    # PRODUITS
    # =====================================================

    products = relationship(
        "Product",
        back_populates="boutique"
    )