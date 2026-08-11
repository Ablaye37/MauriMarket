from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.subcategory import SubCategory
from app.models.product import Product


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# API : SOUS-CATÉGORIES D'UNE CATÉGORIE
# =====================================================

@router.get("/api/categorie/{category_id}/sous-categories")
async def get_sous_categories(category_id: int):

    db = SessionLocal()

    try:

        subcategories = (
            db.query(SubCategory)
            .filter(
                SubCategory.category_id == category_id
            )
            .order_by(SubCategory.id)
            .all()
        )

        return [
            {
                "id": subcategory.id,
                "name": subcategory.name
            }
            for subcategory in subcategories
        ]

    finally:

        db.close()


# =====================================================
# AFFICHER LES PRODUITS D'UNE SOUS-CATÉGORIE
# =====================================================

@router.get("/sous-categorie/{subcategory_id}")
async def afficher_sous_categorie(
    request: Request,
    subcategory_id: int
):

    db = SessionLocal()

    try:

        subcategory = (
            db.query(SubCategory)
            .filter(
                SubCategory.id == subcategory_id
            )
            .first()
        )

        if not subcategory:

            return {
                "error": "Sous-catégorie introuvable"
            }

        products = (
            db.query(Product)
            .filter(
                Product.subcategory_id == subcategory_id
            )
            .order_by(Product.id.desc())
            .all()
        )

        return templates.TemplateResponse(
            request=request,
            name="sous_categorie.html",
            context={
                "subcategory": subcategory,
                "products": products
            }
        )

    finally:

        db.close()
