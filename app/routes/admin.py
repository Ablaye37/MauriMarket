from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.database.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from sqlalchemy.orm import joinedload
from app.models.category import Category

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =====================================================
# VÉRIFIER ADMIN
# =====================================================

def get_admin(request: Request, db):

    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user or user.role != "admin":
        return None

    return user


# =====================================================
# PAGE ADMIN
# =====================================================

@router.get("/admin")
async def admin_page(request: Request):

    db = SessionLocal()

    admin = get_admin(request, db)

    if not admin:
        db.close()

        return RedirectResponse(
            "/login",
            status_code=303
        )

    users = (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )
    products = (
    db.query(Product)
    .options(
        joinedload(Product.user),
        joinedload(Product.category)
    )
    .order_by(Product.id.desc())
    .all()
)
    user_count = db.query(User).count()
    product_count = db.query(Product).count()
    category_count = db.query(Category).count()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
      context={
    "user": admin,
    "users": users,
    "products": products,
    "user_count": user_count,
    "product_count": product_count,
    "category_count": category_count
}
    )


# =====================================================
# SUPPRIMER UN UTILISATEUR
# =====================================================

@router.post("/admin/utilisateur/supprimer/{user_id}")
async def supprimer_utilisateur(
    request: Request,
    user_id: int
):

    db = SessionLocal()

    admin = get_admin(request, db)

    if not admin:
        db.close()

        return RedirectResponse(
            "/login",
            status_code=303
        )
    
# =====================================================
# CHANGER LE RÔLE D'UN UTILISATEUR
# =====================================================

@router.post("/admin/utilisateur/role/{user_id}")
async def changer_role(
    request: Request,
    user_id: int
):

    db = SessionLocal()

    admin = get_admin(request, db)

    if not admin:
        db.close()

        return RedirectResponse(
            "/login",
            status_code=303
        )

    # Empêcher l'admin de modifier son propre rôle
    if user_id == admin.id:

        db.close()

        request.session["message"] = (
            "❌ Vous ne pouvez pas modifier votre propre rôle."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        db.close()

        request.session["message"] = (
            "❌ Utilisateur introuvable."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    # Changer le rôle
    if user.role == "admin":

        user.role = "user"

        message = (
            f"✅ {user.full_name} est maintenant un utilisateur."
        )

    else:

        user.role = "admin"

        message = (
            f"👑 {user.full_name} est maintenant administrateur."
        )

    db.commit()
    db.close()

    request.session["message"] = message

    return RedirectResponse(
        "/admin",
        status_code=303
    )

# =====================================================
# SUPPRIMER UNE ANNONCE
# =====================================================

@router.post("/admin/annonce/supprimer/{product_id}")
async def supprimer_annonce(
    request: Request,
    product_id: int
):

    db = SessionLocal()

    admin = get_admin(request, db)

    if not admin:
        db.close()

        return RedirectResponse(
            "/login",
            status_code=303
        )

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:

        db.close()

        request.session["message"] = (
            "❌ Annonce introuvable."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    db.delete(product)
    db.commit()
    db.close()

    request.session["message"] = (
        "✅ Annonce supprimée avec succès."
    )

    return RedirectResponse(
        "/admin",
        status_code=303
    )


