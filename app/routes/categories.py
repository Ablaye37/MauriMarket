from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.product import Product

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =====================================================
# AFFICHER UNE CATÉGORIE
# =====================================================

@router.get("/categorie/{category_id}")
async def afficher_categorie(
    request: Request,
    category_id: int
):
    db = SessionLocal()

    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        db.close()
        return {"error": "Catégorie introuvable"}

    subcategories = (
        db.query(SubCategory)
        .filter(SubCategory.category_id == category_id)
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="categorie.html",
        context={
            "category": category,
            "subcategories": subcategories
        }
    )


# =====================================================
# AFFICHER UNE SOUS-CATÉGORIE
# =====================================================

@router.get("/sous-categorie/{subcategory_id}")
async def afficher_sous_categorie(
    request: Request,
    subcategory_id: int
):
    db = SessionLocal()

    subcategory = (
        db.query(SubCategory)
        .filter(SubCategory.id == subcategory_id)
        .first()
    )

    if not subcategory:
        db.close()
        return {"error": "Sous-catégorie introuvable"}

    products = (
        db.query(Product)
        .filter(
            Product.subcategory_id == subcategory_id
        )
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sous_categorie.html",
        context={
            "subcategory": subcategory,
            "products": products
        }
    )