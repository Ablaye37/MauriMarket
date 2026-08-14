
from app.database.database import engine, Base, SessionLocal

from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.product import Product
from app.models.user import User




def init_database():

    print("Création des tables...")

    # =====================================================
    # CRÉATION DES TABLES
    # =====================================================

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # =====================================================
    # AJOUT DU RÔLE AUX UTILISATEURS
    # =====================================================




    # =====================================================
    # CATALOGUE MAURIMARKET
    # =====================================================

    catalogue = {

        "Téléphones & Tablettes": [
            "iPhone",
            "Samsung",
            "Xiaomi",
            "Tecno",
            "Infinix",
            "Huawei",
            "Oppo",
            "Autres téléphones",
            "Tablettes",
            "Montres connectées"
        ],

        "Informatique": [
            "Ordinateurs portables",
            "Ordinateurs de bureau",
            "MacBook",
            "PC Gaming",
            "Écrans",
            "Claviers & souris",
            "Imprimantes",
            "Disques durs & SSD",
            "RAM",
            "Cartes graphiques",
            "Accessoires informatiques",
            "Réseaux & Wi-Fi"
        ],

        "Véhicules": [
            "Voitures",
            "Motos",
            "Camions",
            "Bus",
            "Pièces automobiles",
            "Pneus",
            "Accessoires auto",
            "Accessoires moto"
        ],

        "Mode": [
            "Mode Homme",
            "Mode Femme",
            "Chaussures",
            "Sacs",
            "Montres",
            "Bijoux",
            "Accessoires"
        ],

        "Maison & Électroménager": [
            "Réfrigérateurs",
            "Congélateurs",
            "Télévisions",
            "Climatiseurs",
            "Ventilateurs",
            "Machines à laver",
            "Cuisinières",
            "Micro-ondes",
            "Meubles",
            "Décoration",
            "Cuisine",
            "Literie"
        ],

        "Gaming & Divertissement": [
            "PlayStation",
            "Xbox",
            "Nintendo",
            "Jeux vidéo",
            "Manettes",
            "Casques gaming",
            "Accessoires gaming"
        ],

        "Enfants & Bébés": [
            "Vêtements garçons",
            "Vêtements filles",
            "Chaussures enfants",
            "Jouets",
            "Poussettes",
            "Articles pour bébé",
            "Fournitures scolaires"
        ],

        "Services": [
            "Transport",
            "Livraison",
            "Réparation",
            "Informatique",
            "Formation",
            "Services professionnels"
        ],

        "Immobilier": [
            "Maisons",
            "Appartements",
            "Terrains",
            "Bureaux",
            "Locaux commerciaux",
            "Locations"
        ]
    }

    # =====================================================
    # CRÉATION DES CATÉGORIES ET SOUS-CATÉGORIES
    # =====================================================

    for category_name, subcategories in catalogue.items():

        category = (
            db.query(Category)
            .filter(Category.name == category_name)
            .first()
        )

        if not category:

            category = Category(
                name=category_name
            )

            db.add(category)
            db.commit()
            db.refresh(category)

            print(
                f"Catégorie créée : {category_name}"
            )

        for subcategory_name in subcategories:

            existing_subcategory = (
                db.query(SubCategory)
                .filter(
                    SubCategory.name == subcategory_name,
                    SubCategory.category_id == category.id
                )
                .first()
            )

            if not existing_subcategory:

                subcategory = SubCategory(
                    name=subcategory_name,
                    category_id=category.id
                )

                db.add(subcategory)

                print(
                    f"  Sous-catégorie créée : "
                    f"{subcategory_name}"
                )

        db.commit()

    # =====================================================
    # MIGRATION DES ANCIENNES CATÉGORIES
    # =====================================================

    migrations = {
        "Téléphones": "Téléphones & Tablettes",
        "Maison": "Maison & Électroménager"
    }

    for old_name, new_name in migrations.items():

        old_category = (
            db.query(Category)
            .filter(Category.name == old_name)
            .first()
        )

        new_category = (
            db.query(Category)
            .filter(Category.name == new_name)
            .first()
        )

        if old_category and new_category:

            print(
                f"Migration : {old_name} → {new_name}"
            )

            products = (
                db.query(Product)
                .filter(
                    Product.category_id == old_category.id
                )
                .all()
            )

            for product in products:

                product.category_id = new_category.id
                product.subcategory_id = None

            db.commit()

            remaining_products = (
                db.query(Product)
                .filter(
                    Product.category_id == old_category.id
                )
                .count()
            )

            if remaining_products == 0:

                db.delete(old_category)
                db.commit()

                print(
                    f"Ancienne catégorie supprimée : "
                    f"{old_name}"
                )

    # =====================================================
    # SUPPRESSION DES AUTRES ANCIENNES CATÉGORIES
    # =====================================================

    categories_existantes = (
        db.query(Category).all()
    )

    for category in categories_existantes:

        if category.name not in catalogue:

            product_count = (
                db.query(Product)
                .filter(
                    Product.category_id == category.id
                )
                .count()
            )

            if product_count == 0:

                print(
                    f"Suppression ancienne catégorie : "
                    f"{category.name}"
                )

                db.delete(category)
                db.commit()

            else:

                print(
                    f"ATTENTION : catégorie conservée "
                    f"car elle contient "
                    f"{product_count} produit(s) : "
                    f"{category.name}"
                )

    # =====================================================
    # FIN
    # =====================================================

    db.close()

    print("Base prête !")

