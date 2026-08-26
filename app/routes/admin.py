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
from app.models.order_item import OrderItem


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# VÉRIFIER ADMIN
# ============================================================

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


# ============================================================
# REDIRECTION ADMIN
# ============================================================

def admin_redirect():

    return RedirectResponse(
        "/admin",
        status_code=303
    )


# ============================================================
# PAGE ADMIN
# ============================================================

@router.get("/admin")
async def admin_page(
    request: Request
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # VÉRIFIER ADMIN
        # ----------------------------------------------------

        admin = get_admin(
            request,
            db
        )

        if not admin:

            return RedirectResponse(
                "/login",
                status_code=303
            )

        # ====================================================
        # UTILISATEURS
        # ====================================================

        users = (
            db.query(User)
            .order_by(
                User.id.desc()
            )
            .all()
        )

        # ====================================================
        # ANNONCES
        #
        # IMPORTANT :
        # On récupère TOUTES les annonces.
        #
        # Même :
        # - is_active = True
        # - is_active = False
        # - annonces indépendantes
        # - annonces de boutique
        #
        # Donc une annonce présente en base ne sera pas
        # cachée de l'administration.
        # ====================================================
        products = (
        db.query(Product)
        .options(
         joinedload(Product.user),
        joinedload(Product.category),
        joinedload(Product.subcategory),
        joinedload(Product.boutique)
    )
    .filter(
        Product.is_active == True
    )
    .order_by(
        Product.id.desc()
    )
    .all()
)
        # ====================================================
        # BOUTIQUES
        # ====================================================

        boutiques = (
            db.query(Boutique)
            .options(
                joinedload(Boutique.user)
            )
            .order_by(
                Boutique.id.desc()
            )
            .all()
        )

        # ====================================================
        # DEMANDES DE BOUTIQUES
        # ====================================================

        boutique_requests = (
            db.query(BoutiqueRequest)
            .order_by(
                BoutiqueRequest.id.desc()
            )
            .all()
        )

        # ====================================================
        # MESSAGES CONTACT
        # ====================================================

        contact_messages = (
            db.query(ContactMessage)
            .order_by(
                ContactMessage.id.desc()
            )
            .all()
        )

        # ====================================================
        # STATISTIQUES
        # ====================================================

        user_count = (
            db.query(User)
            .count()
        )

        # Toutes les annonces
        product_count = (
            db.query(Product)
            .count()
        )

        # Annonces actuellement visibles
        active_product_count = (
            db.query(Product)
            .filter(
                Product.is_active == True
            )
            .count()
        )

        # Annonces désactivées
        inactive_product_count = (
            db.query(Product)
            .filter(
                Product.is_active == False
            )
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

        contact_message_count = (
            db.query(ContactMessage)
            .filter(
                ContactMessage.status == "new"
            )
            .count()
        )

        # ====================================================
        # MESSAGE FLASH
        # ====================================================

        message = request.session.pop(
            "message",
            None
        )

        # ====================================================
        # AFFICHER ADMIN
        # ====================================================

        return templates.TemplateResponse(

            request=request,

            name="admin.html",

            context={

                "user": admin,

                "users": users,

                "products": products,

                "boutiques": boutiques,

                "boutique_requests":
                    boutique_requests,

                "contact_messages":
                    contact_messages,

                "user_count":
                    user_count,

                "product_count":
                    product_count,

                "active_product_count":
                    active_product_count,

                "inactive_product_count":
                    inactive_product_count,

                "category_count":
                    category_count,

                "boutique_count":
                    boutique_count,

                "boutique_request_count":
                    boutique_request_count,

                "contact_message_count":
                    contact_message_count,

                "message":
                    message
            }
        )

    except Exception as e:

        print(
            "❌ ERREUR PAGE ADMIN :",
            repr(e)
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


# ============================================================
# SUPPRIMER UN UTILISATEUR
# ============================================================

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

        # ----------------------------------------------------
        # EMPÊCHER L'ADMIN DE SE SUPPRIMER
        # ----------------------------------------------------

        if user_id == admin.id:

            request.session["message"] = (
                "❌ Vous ne pouvez pas supprimer "
                "votre propre compte."
            )

            return admin_redirect()

        # ----------------------------------------------------
        # UTILISATEUR
        # ----------------------------------------------------

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

            return admin_redirect()

        user_name = user.full_name

        # ----------------------------------------------------
        # SUPPRIMER SES PRODUITS
        # ----------------------------------------------------

        products = (
            db.query(Product)
            .filter(
                Product.user_id == user.id
            )
            .all()
        )

        for product in products:

            db.delete(product)

        # ----------------------------------------------------
        # SUPPRIMER SES BOUTIQUES
        # ----------------------------------------------------

        boutiques = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user.id
            )
            .all()
        )

        for boutique in boutiques:

            db.delete(boutique)

        # ----------------------------------------------------
        # SUPPRIMER SES DEMANDES
        # ----------------------------------------------------

        requests_list = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.user_id == user.id
            )
            .all()
        )

        for boutique_request in requests_list:

            db.delete(boutique_request)

        # ----------------------------------------------------
        # SUPPRIMER UTILISATEUR
        # ----------------------------------------------------

        db.delete(user)

        db.commit()

        request.session["message"] = (
            f"✅ Utilisateur {user_name} "
            "et toutes ses données ont été supprimés."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR SUPPRESSION UTILISATEUR :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "cet utilisateur. "
            "Vérifiez les relations de la base."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# CHANGER LE RÔLE
# ============================================================

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

        if user_id == admin.id:

            request.session["message"] = (
                "❌ Vous ne pouvez pas modifier "
                "votre propre rôle."
            )

            return admin_redirect()

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

            return admin_redirect()

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

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR CHANGEMENT ROLE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de modifier "
            "le rôle."
        )

        return admin_redirect()

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

        # -------------------------------------------------
        # VÉRIFIER ADMIN
        # -------------------------------------------------

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
        # CHERCHER L'ANNONCE
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

        print(
            f"🗑️ Tentative suppression : "
            f"{product.id} {product.title}"
        )

        # -------------------------------------------------
        # VÉRIFIER SI LE PRODUIT EST UTILISÉ
        # DANS UNE COMMANDE
        # -------------------------------------------------

        order_item = (
            db.query(OrderItem)
            .filter(
                OrderItem.product_id == product.id
            )
            .first()
        )

        # -------------------------------------------------
        # CAS 1 :
        # PRODUIT UTILISÉ DANS UNE COMMANDE
        # -------------------------------------------------

        if order_item:

            # On ne peut pas supprimer physiquement
            # le produit car order_items.product_id
            # pointe encore vers products.id.

            product.is_active = False

            db.commit()

            print(
                f"⚠️ Produit #{product.id} conservé "
                "car il est utilisé dans une commande."
            )

            request.session["message"] = (
                f"⛔ Annonce « {product_title} » "
                "désactivée. Elle est conservée dans "
                "la base afin de préserver l'historique "
                "des commandes."
            )

            return RedirectResponse(
                "/admin",
                status_code=303
            )

        # -------------------------------------------------
        # CAS 2 :
        # PRODUIT JAMAIS UTILISÉ DANS UNE COMMANDE
        # -------------------------------------------------

        db.delete(product)

        db.commit()

        print(
            f"✅ Produit #{product.id} "
            "supprimé définitivement."
        )

        request.session["message"] = (
            f"🗑️ Annonce « {product_title} » "
            "supprimée définitivement."
        )

        return RedirectResponse(
            "/admin",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR SUPPRESSION ANNONCE ADMIN :",
            repr(e)
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

# ============================================================
# RÉACTIVER UNE ANNONCE
# ============================================================

@router.post(
    "/admin/annonce/reactiver/{product_id}"
)
async def reactiver_annonce(

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

            return admin_redirect()

        product.is_active = True

        db.commit()

        request.session["message"] = (
            f"✅ Annonce « {product.title} » "
            "réactivée."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR RÉACTIVATION :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de réactiver "
            "cette annonce."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# DÉSACTIVER UNE ANNONCE
# ============================================================

@router.post(
    "/admin/annonce/desactiver/{product_id}"
)
async def desactiver_annonce(

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

            return admin_redirect()

            product_title = product.title

            db.delete(product)
            db.commit()
            request.session["message"] = (
            f"🗑️ Annonce « {product_title} » "
            "supprimée définitivement."
          )
        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR DÉSACTIVATION :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de désactiver "
            "cette annonce."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# SUPPRIMER UNE BOUTIQUE
# ============================================================

@router.post(
    "/admin/boutique/supprimer/{boutique_id}"
)
async def supprimer_boutique(

    request: Request,

    boutique_id: int
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

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.id == boutique_id
            )
            .first()
        )

        if not boutique:

            request.session["message"] = (
                "❌ Boutique introuvable."
            )

            return admin_redirect()

        boutique_name = boutique.name

        # ----------------------------------------------------
        # PRODUITS DE LA BOUTIQUE
        # ----------------------------------------------------

        products = (
            db.query(Product)
            .filter(
                Product.boutique_id == boutique.id
            )
            .all()
        )

        for product in products:

            db.delete(product)

        # ----------------------------------------------------
        # SUPPRIMER BOUTIQUE
        # ----------------------------------------------------

        db.delete(boutique)

        db.commit()

        request.session["message"] = (
            f"🗑️ Boutique « {boutique_name} » "
            "et ses annonces ont été supprimées."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR SUPPRESSION BOUTIQUE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "cette boutique."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# ACCEPTER UNE DEMANDE DE BOUTIQUE
# ============================================================

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

            return admin_redirect()

        if boutique_request.status != "pending":

            request.session["message"] = (
                "⚠️ Cette demande a déjà "
                "été traitée."
            )

            return admin_redirect()

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

            return admin_redirect()

        boutique = Boutique(

            name=boutique_request.name,

            sale_type=boutique_request.sale_type,

            user_id=boutique_request.user_id
        )

        db.add(boutique)

        boutique_request.status = "approved"

        db.commit()

        request.session["message"] = (
            "✅ Demande de boutique "
            "acceptée et boutique créée."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR ACCEPTATION BOUTIQUE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible d'accepter "
            "cette demande."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# REFUSER UNE DEMANDE DE BOUTIQUE
# ============================================================

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

            return admin_redirect()

        if boutique_request.status != "pending":

            request.session["message"] = (
                "⚠️ Cette demande a déjà "
                "été traitée."
            )

            return admin_redirect()

        boutique_request.status = "rejected"

        db.commit()

        request.session["message"] = (
            "❌ Demande de boutique refusée."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR REFUS BOUTIQUE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de refuser "
            "cette demande."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# SUPPRIMER UNE DEMANDE DE BOUTIQUE
# ============================================================

@router.post(
    "/admin/boutique/demande/supprimer/{request_id}"
)
async def supprimer_demande_boutique(

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

        boutique_request = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.id == request_id
            )
            .first()
        )

        if not boutique_request:

            request.session["message"] = (
                "❌ Demande introuvable."
            )

            return admin_redirect()

        db.delete(
            boutique_request
        )

        db.commit()

        request.session["message"] = (
            "🗑️ Demande de boutique "
            "supprimée définitivement."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR SUPPRESSION DEMANDE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "cette demande."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# MARQUER MESSAGE COMME LU
# ============================================================

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

            return admin_redirect()

        contact_message.status = "read"

        db.commit()

        request.session["message"] = (
            "✅ Message marqué comme lu."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR LECTURE MESSAGE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de modifier "
            "le message."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# REMETTRE MESSAGE COMME NON LU
# ============================================================

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

            return admin_redirect()

        contact_message.status = "new"

        db.commit()

        request.session["message"] = (
            "📩 Message marqué comme non lu."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR MESSAGE NON LU :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de modifier "
            "le message."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# SUPPRIMER MESSAGE CONTACT
# ============================================================

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

            return admin_redirect()

        message_name = (
            contact_message.name
        )

        db.delete(
            contact_message
        )

        db.commit()

        request.session["message"] = (
            f"🗑️ Message de {message_name} "
            "supprimé avec succès."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR SUPPRESSION MESSAGE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "ce message."
        )

        return admin_redirect()

    finally:

        db.close()