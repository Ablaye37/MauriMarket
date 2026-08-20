from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database.database import Base


class ContactMessage(Base):

    __tablename__ = "contact_messages"

    # =====================================================
    # IDENTIFIANT
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # INFORMATIONS DU CONTACT
    # =====================================================

    name = Column(
        String(100),
        nullable=False
    )

    phone = Column(
        String(30),
        nullable=False
    )

    email = Column(
        String(150),
        nullable=True
    )

    # =====================================================
    # MESSAGE
    # =====================================================

    subject = Column(
        String(200),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    # =====================================================
    # STATUT
    # =====================================================

    status = Column(
        String(20),
        nullable=False,
        default="new"
    )

    # =====================================================
    # DATE DE CRÉATION
    # =====================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )