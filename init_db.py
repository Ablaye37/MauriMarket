from app.database.database import Base, engine

from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.product import Product
from app.models.user import User
from app.models.boutique import Boutique
from app.models.boutique_request import BoutiqueRequest
from app.models.contact_message import ContactMessage


# =====================================================
# CRÉER LES TABLES
# =====================================================

Base.metadata.create_all(
    bind=engine
)


print("✅ Base de données créée avec succès !")