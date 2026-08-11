from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.product import Product


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.post("/panier/ajouter/{product_id}")
async def ajouter_au_panier(request: Request, product_id: int):

    db = SessionLocal()

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    db.close()

    if not product:
        request.session["message"] = "Produit introuvable"

        return RedirectResponse(
            url="/",
            status_code=303
        )

    panier = request.session.get("panier", [])

    if product_id not in panier:
        panier.append(product_id)

    request.session["panier"] = panier

    request.session["message"] = "Produit ajouté au panier"

    return RedirectResponse(
        url=f"/produit/{product_id}",
        status_code=303
    )


@router.get("/panier")
async def afficher_panier(request: Request):

    panier = request.session.get("panier", [])

    db = SessionLocal()

    if panier:
        products = (
            db.query(Product)
            .filter(Product.id.in_(panier))
            .all()
        )
    else:
        products = []

    total = sum(
        product.price or 0
        for product in products
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="panier.html",
        context={
            "products": products,
            "total": total
        }
    )


@router.get("/panier/supprimer/{product_id}")
async def supprimer_du_panier(
    request: Request,
    product_id: int
):

    panier = request.session.get("panier", [])

    if product_id in panier:
        panier.remove(product_id)

    request.session["panier"] = panier

    return RedirectResponse(
        url="/panier",
        status_code=303
    )