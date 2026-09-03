from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class OrderItem(Base):

    __tablename__ = "order_items"

    # ============================================================
    # IDENTIFIANT
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================================================
    # COMMANDE
    # ============================================================

    order_id = Column(
        Integer,
        ForeignKey(
            "orders.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ============================================================
    # PRODUIT
    #
    # nullable=True :
    # permet de supprimer définitivement un produit tout en
    # conservant l'historique de la commande.
    # ============================================================

    product_id = Column(
        Integer,
        ForeignKey(
            "products.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # ============================================================
    # SNAPSHOT DU PRODUIT
    # ============================================================

    product_title = Column(
        String(200),
        nullable=False
    )

    price = Column(
        Float,
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False,
        default=1
    )

    subtotal = Column(
        Float,
        nullable=False
    )

    # ============================================================
    # RELATION COMMANDE
    # ============================================================

    order = relationship(
        "Order",
        back_populates="items"
    )

    # ============================================================
    # RELATION PRODUIT
    #
    # Le produit peut avoir été supprimé.
    # Dans ce cas product sera simplement None.
    # ============================================================

    product = relationship(
        "Product"
    )