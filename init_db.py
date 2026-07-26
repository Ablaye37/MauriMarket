from app.database.database import engine, Base
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.product import Product
# Importer tous les modèles
from app.models.user import User
	

Base.metadata.create_all(bind=engine)

print("✅ Base de données créée avec succès !")
