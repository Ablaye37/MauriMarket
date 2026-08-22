from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    # =====================================================
    # IDENTIFIANT
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # NOM COMPLET
    # =====================================================

    full_name = Column(
        String(100),
        nullable=False
    )

    # =====================================================
    # TÉLÉPHONE
    # =====================================================

    phone = Column(
        String(20),
        unique=True,
        nullable=False
    )

    # =====================================================
    # MOT DE PASSE
    # =====================================================

    password = Column(
        String(255),
        nullable=False
    )

    # =====================================================
    # RÔLE
    # =====================================================

    role = Column(
        String(20),
        nullable=False,
        default="user"
    )

    # =====================================================
    # BOUTIQUE
    #
    # Un utilisateur peut avoir au maximum une boutique.
    # La vérification métier est également faite dans
    # les routes.
    # =====================================================

    boutique = relationship(
        "Boutique",
        back_populates="user",
        uselist=False
    )

    # =====================================================
    # PRODUITS
    # =====================================================

    products = relationship(
        "Product",
        back_populates="user"
    )

    # =====================================================
    # DEMANDES DE BOUTIQUE
    # =====================================================

    boutique_requests = relationship(
        "BoutiqueRequest",
        back_populates="user",
        cascade="all, delete-orphan"
    )