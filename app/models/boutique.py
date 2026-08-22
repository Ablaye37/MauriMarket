from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Boutique(Base):
    __tablename__ = "boutiques"

    # ============================================================
    # IDENTIFIANT
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================================================
    # NOM
    # ============================================================

    name = Column(
        String(150),
        nullable=False
    )

    # ============================================================
    # CATÉGORIE DE LA BOUTIQUE
    #
    # À conserver pour le moment.
    # Cette partie sera traitée séparément.
    # ============================================================

    category = Column(
        String(100),
        nullable=True,
        index=True
    )

    # ============================================================
    # TYPE DE VENTE
    # ============================================================

    sale_type = Column(
        String(100),
        nullable=True
    )

    # ============================================================
    # DESCRIPTION
    # ============================================================

    description = Column(
        Text,
        nullable=True
    )

    # ============================================================
    # VILLE
    # ============================================================

    city = Column(
        String(100),
        nullable=True
    )

    # ============================================================
    # LOGO
    # ============================================================

    logo = Column(
        String(500),
        nullable=True
    )

    # ============================================================
    # IMAGE DE COUVERTURE
    # ============================================================

    cover_image = Column(
        String(500),
        nullable=True
    )

    # ============================================================
    # PROPRIÉTAIRE
    # ============================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="boutique"
    )

    # ============================================================
    # PRODUITS DE LA BOUTIQUE
    # ============================================================

    products = relationship(
        "Product",
        back_populates="boutique",
        cascade="all, delete-orphan"
    )