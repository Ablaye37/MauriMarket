from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import joinedload

from app.database.database import SessionLocal
from app.models.user import User
from app.models.product import Product
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

    try:

        admin = get_admin(request, db)

        if not admin:
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

    finally:
        db.close()


# =====================================================
# SUPPRIMER UN UTILISATEUR
# =====================================================

@router.post("/admin/utilisateur/supprimer/{user_id}")
async def supprimer_utilisateur(
    request: Request,
    user_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(request, db)

        if not admin:
            return RedirectResponse(
                "/login",
                status_code=303
            )

        # Empêcher l'admin de se supprimer lui-même
        if user_id == admin.id:

            request.session["message"] = (
                "❌ Vous ne pouvez pas supprimer votre propre compte."
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

            request.session["message"] = (
                "❌ Utilisateur introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # Supprimer les annonces de l'utilisateur
        # -------------------------------------------------

        products = (
            db.query(Product)
            .filter(Product.user_id == user.id)
            .all()
        )

        for product in products:
            db.delete(product)

        # -------------------------------------------------
        # Supprimer l'utilisateur
        # -------------------------------------------------

        user_name = user.full_name

        db.delete(user)
        db.commit()

        request.session["message"] = (
            f"✅ Utilisateur {user_name} supprimé avec succès."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print("ERREUR SUPPRESSION UTILISATEUR :", e)

        request.session["message"] = (
            "❌ Impossible de supprimer cet utilisateur."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:
        db.close()


# =====================================================
# CHANGER LE RÔLE D'UN UTILISATEUR
# =====================================================

@router.post("/admin/utilisateur/role/{user_id}")
async def changer_role(
    request: Request,
    user_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(request, db)

        if not admin:
            return RedirectResponse(
                "/login",
                status_code=303
            )

        # Empêcher l'admin de modifier son propre rôle
        if user_id == admin.id:

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

            request.session["message"] = (
                "❌ Utilisateur introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # Changer le rôle
        # -------------------------------------------------

        if user.role == "admin":

            user.role = "user"

            message = (
                f"✅ {user.full_name} est maintenant utilisateur."
            )

        else:

            user.role = "admin"

            message = (
                f"👑 {user.full_name} est maintenant administrateur."
            )

        db.commit()

        request.session["message"] = message

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print("ERREUR CHANGEMENT ROLE :", e)

        request.session["message"] = (
            "❌ Impossible de modifier le rôle."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:
        db.close()


# =====================================================
# SUPPRIMER UNE ANNONCE
# =====================================================

@router.post("/admin/annonce/supprimer/{product_id}")
async def supprimer_annonce(
    request: Request,
    product_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(request, db)

        if not admin:
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

            request.session["message"] = (
                "❌ Annonce introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        product_title = product.title

        db.delete(product)
        db.commit()

        request.session["message"] = (
            f"✅ Annonce « {product_title} » supprimée avec succès."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print("ERREUR SUPPRESSION ANNONCE :", e)

        request.session["message"] = (
            "❌ Impossible de supprimer cette annonce."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:
        db.close()
        