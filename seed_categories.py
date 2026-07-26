from app.database.database import SessionLocal
from app.models.category import Category

db = SessionLocal()

categories = [
    {"name": "Électronique", "icon": "bi-phone"},
    {"name": "Véhicules", "icon": "bi-car-front"},
    {"name": "Immobilier", "icon": "bi-house"},
    {"name": "Emploi", "icon": "bi-briefcase"},
    {"name": "Services", "icon": "bi-tools"},
    {"name": "Mode", "icon": "bi-bag"},
]

for category in categories:
    exists = db.query(Category).filter(Category.name == category["name"]).first()

    if not exists:
        db.add(Category(**category))

db.commit()
db.close()

print("✅ Catégories ajoutées avec succès !")
