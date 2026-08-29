from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.favorite import Favorite
from app.models.product import Product


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"]
)


# =====================================================
# TEMPLATES
# =====================================================

templates = Jinja2Templates(
    directory="app/templates"
)

# =====================================================
# AJOUTER / RETIRER UN FAVORI
# =====================================================

@router.post("/toggle/{product_id}")
async def toggle_favorite(
    request: Request,
    product_id: int
):

    # -------------------------------------------------
    # VÉRIFIER LA CONNEXION
    # -------------------------------------------------

    user_id = request.session.get("user_id")

    if not user_id:
        request.session["message"] = (
            "🔐 Connectez-vous pour ajouter un produit aux favoris."
        )

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # VÉRIFIER QUE LE PRODUIT EXISTE
        # -------------------------------------------------

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id,
                Product.is_active == True
            )
            .first()
        )

        if not product:

            request.session["message"] = (
                "❌ Ce produit n'est plus disponible."
            )

            return RedirectResponse(
                "/",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER LE FAVORI
        # -------------------------------------------------

        favorite = (
            db.query(Favorite)
            .filter(
                Favorite.user_id == user_id,
                Favorite.product_id == product_id
            )
            .first()
        )

        # -------------------------------------------------
        # RETIRER
        # -------------------------------------------------

        if favorite:

            db.delete(favorite)
            db.commit()

            request.session["message"] = (
                "💔 Produit retiré des favoris."
            )

        # -------------------------------------------------
        # AJOUTER
        # -------------------------------------------------

        else:

            new_favorite = Favorite(
                user_id=user_id,
                product_id=product_id
            )

            db.add(new_favorite)
            db.commit()

            request.session["message"] = (
                "❤️ Produit ajouté aux favoris."
            )

        # -------------------------------------------------
        # RETOUR
        # -------------------------------------------------

        return RedirectResponse(
            request.headers.get("referer") or "/",
            status_code=303
        )

    finally:

        db.close()
        # =====================================================
# MES FAVORIS
# =====================================================

@router.get("/mes-favoris")
async def mes_favoris(request: Request):

    # -------------------------------------------------
    # VÉRIFIER LA CONNEXION
    # -------------------------------------------------

    user_id = request.session.get("user_id")

    if not user_id:
        request.session["message"] = (
            "🔐 Connectez-vous pour accéder à vos favoris."
        )

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # RÉCUPÉRER LES FAVORIS
        # -------------------------------------------------

        favorites = (
            db.query(Favorite)
            .filter(
                Favorite.user_id == user_id
            )
            .order_by(
                Favorite.created_at.desc()
            )
            .all()
        )

        # -------------------------------------------------
        # MESSAGE
        # -------------------------------------------------

        message = request.session.pop(
            "message",
            None
        )

        # -------------------------------------------------
        # AFFICHER LA PAGE
        # -------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="favoris.html",
            context={
                "favorites": favorites,
                "message": message
            }
        )

    finally:

        db.close()