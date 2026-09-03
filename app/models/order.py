from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Text,
    DateTime
)

from sqlalchemy.orm import relationship

from datetime import datetime

from app.database.database import Base


class Order(Base):

    __tablename__ = "orders"

    # =====================================================
    # IDENTIFIANT
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # NUMÉRO DE COMMANDE
    # =====================================================
    # =====================================================
    # DATE DE CREATION
    # =====================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )


    order_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # =====================================================
    # UTILISATEUR
    #
    # SET NULL permet de conserver la commande même si
    # l'utilisateur est supprimé.
    # =====================================================

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # =====================================================
    # INFORMATIONS CLIENT
    # =====================================================

    customer_name = Column(
        String(100),
        nullable=False
    )

    customer_phone = Column(
        String(30),
        nullable=False
    )

    # =====================================================
    # LIVRAISON
    # =====================================================

    city = Column(
        String(100),
        nullable=False
    )

    delivery_address = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # COMMENTAIRE
    # =====================================================

    comment = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # TOTAL
    # =====================================================

    total = Column(
        Float,
        nullable=False,
        default=0
    )

    # =====================================================
    # STATUT DE LA COMMANDE
    # =====================================================

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True
    )

    # =====================================================
    # STATUT DU PAIEMENT
    # =====================================================

    payment_status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True
    )

    # =====================================================
    # MÉTHODE DE PAIEMENT
    #
    # Paiement manuel à la livraison.
    # =====================================================

    payment_method = Column(
        String(50),
        nullable=True,
        default="manuel"
    )

    # =====================================================
    # STATUT DE LIVRAISON
    #
    # pending    = nouvelle commande
    # pickup     = produit à récupérer chez le vendeur
    # delivering = produit en cours de livraison
    # delivered  = produit livré
    # =====================================================

    delivery_status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True
    )

    # =====================================================
    # LIVREUR
    #
    # Pour le moment, le livreur est toi.
    # =====================================================

    delivery_person = Column(
        String(100),
        nullable=True,
        default="Papa"
    )

    # =====================================================
    # RELATION UTILISATEUR
    # =====================================================

    user = relationship(
        "User",
        back_populates="orders"
    )

    # =====================================================
    # RELATION ARTICLES DE COMMANDE
    # =====================================================

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


