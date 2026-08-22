from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import joinedload

from app.database.database import SessionLocal

from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.boutique import Boutique
from app.models.boutique_request import BoutiqueRequest
from app.models.contact_message import ContactMessage


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


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

    if not user:
        return None

    if user.role != "admin":
        return None

    return user


# =====================================================
# PAGE ADMIN
# =====================================================

@router.get("/admin")
async def admin_page(request: Request):

    db = SessionLocal()

    try:

        # =================================================
        # VÉRIFIER ADMIN
        # =================================================

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # =================================================
        # UTILISATEURS
        # =================================================

        users = (
            db.query(User)
            .order_by(
                User.id.desc()
            )
            .all()
        )

        # =================================================
        # ANNONCES
        # =================================================

        products = (
            db.query(Product)
            .options(
                joinedload(Product.user),
                joinedload(Product.category)
            )
            .order_by(
                Product.id.desc()
            )
            .all()
        )

        # =================================================
        # DEMANDES DE BOUTIQUES
        # =================================================

        boutique_requests = (
            db.query(BoutiqueRequest)
            .order_by(
                BoutiqueRequest.id.desc()
            )
            .all()
        )

        # =================================================
        # MESSAGES CONTACT
        # =================================================

        contact_messages = (
            db.query(ContactMessage)
            .order_by(
                ContactMessage.id.desc()
            )
            .all()
        )

        # Nombre de messages non lus
        contact_message_count = (
            db.query(ContactMessage)
            .filter(
                ContactMessage.status == "new"
            )
            .count()
        )

        # =================================================
        # STATISTIQUES
        # =================================================

        user_count = (
            db.query(User)
            .count()
        )

        product_count = (
            db.query(Product)
            .count()
        )

        category_count = (
            db.query(Category)
            .count()
        )

        boutique_count = (
            db.query(Boutique)
            .count()
        )

        boutique_request_count = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.status == "pending"
            )
            .count()
        )

        # =================================================
        # MESSAGE FLASH
        # =================================================

        message = request.session.pop(
            "message",
            None
        )

        # =================================================
        # AFFICHER PAGE ADMIN
        # =================================================

        return templates.TemplateResponse(
            request=request,
            name="admin.html",
            context={

                # ADMIN
                "user": admin,

                # UTILISATEURS
                "users": users,

                # PRODUITS
                "products": products,

                # BOUTIQUES
                "boutique_requests": boutique_requests,

                # CONTACT
                "contact_messages": contact_messages,

                # STATISTIQUES
                "user_count": user_count,
                "product_count": product_count,
                "category_count": category_count,
                "boutique_count": boutique_count,
                "boutique_request_count": boutique_request_count,
                "contact_message_count": contact_message_count,

                # MESSAGE
                "message": message
            }
        )

    except Exception as e:

        print(
            "ERREUR PAGE ADMIN :",
            e
        )

        request.session["message"] = (
            "❌ Une erreur est survenue "
            "sur la page administrateur."
        )

        return RedirectResponse(
            "/",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# SUPPRIMER UN UTILISATEUR
# =====================================================

@router.post(
    "/admin/utilisateur/supprimer/{user_id}"
)
async def supprimer_utilisateur(
    request: Request,
    user_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # EMPÊCHER L'ADMIN DE SE SUPPRIMER
        # -------------------------------------------------

        if user_id == admin.id:

            request.session["message"] = (
                "❌ Vous ne pouvez pas supprimer "
                "votre propre compte."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER UTILISATEUR
        # -------------------------------------------------

        user = (
            db.query(User)
            .filter(
                User.id == user_id
            )
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

        user_name = user.full_name

        # -------------------------------------------------
        # SUPPRIMER SES PRODUITS
        # -------------------------------------------------

        products = (
            db.query(Product)
            .filter(
                Product.user_id == user.id
            )
            .all()
        )

        for product in products:
            db.delete(product)

        # -------------------------------------------------
        # SUPPRIMER SES BOUTIQUES
        # -------------------------------------------------

        boutiques = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user.id
            )
            .all()
        )

        for boutique in boutiques:
            db.delete(boutique)

        # -------------------------------------------------
        # SUPPRIMER SES DEMANDES DE BOUTIQUE
        # -------------------------------------------------

        boutique_requests = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.user_id == user.id
            )
            .all()
        )

        for boutique_request in boutique_requests:
            db.delete(boutique_request)

        # -------------------------------------------------
        # SUPPRIMER UTILISATEUR
        # -------------------------------------------------

        db.delete(user)

        db.commit()

        request.session["message"] = (
            f"✅ Utilisateur {user_name} "
            "supprimé avec succès."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR SUPPRESSION UTILISATEUR :",
            e
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "cet utilisateur."
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

@router.post(
    "/admin/utilisateur/role/{user_id}"
)
async def changer_role(
    request: Request,
    user_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # EMPÊCHER LA MODIFICATION DE SON PROPRE RÔLE
        # -------------------------------------------------

        if user_id == admin.id:

            request.session["message"] = (
                "❌ Vous ne pouvez pas modifier "
                "votre propre rôle."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER UTILISATEUR
        # -------------------------------------------------

        user = (
            db.query(User)
            .filter(
                User.id == user_id
            )
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
        # CHANGER RÔLE
        # -------------------------------------------------

        if user.role == "admin":

            user.role = "user"

            message = (
                f"✅ {user.full_name} "
                "est maintenant utilisateur."
            )

        else:

            user.role = "admin"

            message = (
                f"👑 {user.full_name} "
                "est maintenant administrateur."
            )

        db.commit()

        request.session["message"] = message

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR CHANGEMENT ROLE :",
            e
        )

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

@router.post(
    "/admin/annonce/supprimer/{product_id}"
)
async def supprimer_annonce(
    request: Request,
    product_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER PRODUIT
        # -------------------------------------------------

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
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

        # -------------------------------------------------
        # SUPPRIMER
        # -------------------------------------------------

        db.delete(product)

        db.commit()

        request.session["message"] = (
            f"✅ Annonce « {product_title} » "
            "supprimée avec succès."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR SUPPRESSION ANNONCE :",
            e
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "cette annonce."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# ACCEPTER UNE DEMANDE DE BOUTIQUE
# =====================================================

@router.post(
    "/admin/boutique/accepter/{request_id}"
)
async def accepter_boutique(
    request: Request,
    request_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER LA DEMANDE
        # -------------------------------------------------

        boutique_request = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.id == request_id
            )
            .first()
        )

        if not boutique_request:

            request.session["message"] = (
                "❌ Demande de boutique "
                "introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # VÉRIFIER STATUT
        # -------------------------------------------------

        if boutique_request.status != "pending":

            request.session["message"] = (
                "⚠️ Cette demande a déjà "
                "été traitée."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # VÉRIFIER SI L'UTILISATEUR A DÉJÀ UNE BOUTIQUE
        # -------------------------------------------------

        boutique_existante = (
            db.query(Boutique)
            .filter(
                Boutique.user_id
                == boutique_request.user_id
            )
            .first()
        )

        if boutique_existante:

            boutique_request.status = "approved"

            db.commit()

            request.session["message"] = (
                "⚠️ L'utilisateur possède "
                "déjà une boutique."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

            # =====================================================
            #       CRÉER LA BOUTIQUE
            # =====================================================

            boutique = Boutique(
            name=boutique_request.name,
            category=boutique_request.category,
            sale_type=boutique_request.sale_type,
             user_id=boutique_request.user_id
              )

            db.add(boutique)
        # -------------------------------------------------
        # APPROUVER
        # -------------------------------------------------

        boutique_request.status = "approved"

        db.commit()

        request.session["message"] = (
            "✅ Demande de boutique "
            "acceptée avec succès."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR ACCEPTATION BOUTIQUE :",
            e
        )

        request.session["message"] = (
            "❌ Impossible d'accepter "
            "cette demande."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# REFUSER UNE DEMANDE DE BOUTIQUE
# =====================================================

@router.post(
    "/admin/boutique/refuser/{request_id}"
)
async def refuser_boutique(
    request: Request,
    request_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER LA DEMANDE
        # -------------------------------------------------

        boutique_request = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.id == request_id
            )
            .first()
        )

        if not boutique_request:

            request.session["message"] = (
                "❌ Demande de boutique "
                "introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # VÉRIFIER STATUT
        # -------------------------------------------------

        if boutique_request.status != "pending":

            request.session["message"] = (
                "⚠️ Cette demande a déjà "
                "été traitée."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # REFUSER
        # -------------------------------------------------

        boutique_request.status = "rejected"

        db.commit()

        request.session["message"] = (
            "❌ Demande de boutique refusée."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR REFUS BOUTIQUE :",
            e
        )

        request.session["message"] = (
            "❌ Impossible de refuser "
            "cette demande."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# MARQUER UN MESSAGE CONTACT COMME LU
# =====================================================

@router.post(
    "/admin/contact/lire/{message_id}"
)
async def lire_message_contact(
    request: Request,
    message_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER MESSAGE
        # -------------------------------------------------

        contact_message = (
            db.query(ContactMessage)
            .filter(
                ContactMessage.id == message_id
            )
            .first()
        )

        if not contact_message:

            request.session["message"] = (
                "❌ Message introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # MARQUER COMME LU
        # -------------------------------------------------

        contact_message.status = "read"

        db.commit()

        request.session["message"] = (
            "✅ Message marqué comme lu."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR LECTURE MESSAGE CONTACT :",
            e
        )

        request.session["message"] = (
            "❌ Impossible de modifier "
            "le message."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# REMETTRE UN MESSAGE COMME NON LU
# =====================================================

@router.post(
    "/admin/contact/non-lu/{message_id}"
)
async def message_contact_non_lu(
    request: Request,
    message_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER MESSAGE
        # -------------------------------------------------

        contact_message = (
            db.query(ContactMessage)
            .filter(
                ContactMessage.id == message_id
            )
            .first()
        )

        if not contact_message:

            request.session["message"] = (
                "❌ Message introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # MARQUER COMME NON LU
        # -------------------------------------------------

        contact_message.status = "new"

        db.commit()

        request.session["message"] = (
            "📩 Message marqué comme non lu."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR MESSAGE NON LU :",
            e
        )

        request.session["message"] = (
            "❌ Impossible de modifier "
            "le message."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# SUPPRIMER UN MESSAGE CONTACT
# =====================================================

@router.post(
    "/admin/contact/supprimer/{message_id}"
)
async def supprimer_message_contact(
    request: Request,
    message_id: int
):

    db = SessionLocal()

    try:

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # -------------------------------------------------
        # CHERCHER MESSAGE
        # -------------------------------------------------

        contact_message = (
            db.query(ContactMessage)
            .filter(
                ContactMessage.id == message_id
            )
            .first()
        )

        if not contact_message:

            request.session["message"] = (
                "❌ Message introuvable."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        message_name = contact_message.name

        # -------------------------------------------------
        # SUPPRIMER
        # -------------------------------------------------

        db.delete(contact_message)

        db.commit()

        request.session["message"] = (
            f"🗑️ Message de {message_name} "
            "supprimé avec succès."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR SUPPRESSION MESSAGE CONTACT :",
            e
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "ce message."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    finally:

        db.close()