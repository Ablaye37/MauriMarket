from app.database.database import engine, Base, SessionLocal
from app.models.category import Category
from app.models.product import Product

def init_database():
    print("Création des tables...")
    
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    if db.query(Category).count() == 0:
        categories = [
            Category(name="Téléphones"),
            Category(name="Informatique"),
            Category(name="Véhicules"),
            Category(name="Mode"),
            Category(name="Maison"),
            Category(name="Services")
        ]

        db.add_all(categories)
        db.commit()

    db.close()
    print("Base prête !")