from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class BoutiqueRequest(Base):
    __tablename__ = "boutique_requests"

    # ============================================================
    # IDENTIFIANT
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================================================
    # NOM DE LA BOUTIQUE
    # ============================================================

    name = Column(
        String(150),
        nullable=False
    )

    # ============================================================
    # CATÉGORIE DE LA BOUTIQUE
    #
    # Cette catégorie est propre à la demande de boutique.
    # Elle est indépendante des catégories des produits.
    #
    # On la conserve pour rester compatible avec la base actuelle.
    # La partie "Catégories" sera traitée séparément.
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
        nullable=False
    )

    # ============================================================
    # STATUT DE LA DEMANDE
    #
    # Exemples :
    # - pending
    # - approved
    # - rejected
    # ============================================================

    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )

    # ============================================================
    # PROPRIÉTAIRE / UTILISATEUR
    # ============================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="boutique_requests"
    )