from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class BoutiqueRequest(Base):

    __tablename__ = "boutique_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    sale_type = Column(
        String(100),
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="boutique_requests"
    )