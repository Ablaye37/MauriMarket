from app.database.database import engine, Base

# Importer tous les modèles
from app.models.user import User

Base.metadata.create_all(bind=engine)

print("✅ Base de données créée avec succès !")
