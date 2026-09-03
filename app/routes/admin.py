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
from app.models.order import Order
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
        .filter(
            User.id == user_id
        )
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
        # PRODUITS
        # ====================================================

        products = (
            db.query(Product)
            .options(
                joinedload(Product.user),
                joinedload(Product.category),
                joinedload(Product.subcategory),
                joinedload(Product.boutique)
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
        # DEMANDES DE BOUTIQUE
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
        # COMMANDES
        # ====================================================

        orders = (
            db.query(Order)
            .options(
                joinedload(Order.user),
                joinedload(Order.items)
                .joinedload(OrderItem.product)
            )
            .order_by(
                Order.created_at.desc()
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

        product_count = (
            db.query(Product)
            .count()
        )

        active_product_count = (
            db.query(Product)
            .filter(
                Product.is_active == True
            )
            .count()
        )

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

        pending_order_count = (
            db.query(Order)
            .filter(
                Order.status == "pending"
            )
            .count()
        )

        # ====================================================
        # LOGS
        # ====================================================

        print("====================================")
        print(
            "📊 TOTAL PRODUITS :",
            product_count
        )
        print(
            "🟢 PRODUITS ACTIFS :",
            active_product_count
        )
        print(
            "🔴 PRODUITS INACTIFS :",
            inactive_product_count
        )
        print(
            "📦 TOTAL COMMANDES :",
            len(orders)
        )
        print(
            "⏳ COMMANDES EN ATTENTE :",
            pending_order_count
        )
        print("====================================")

        # ====================================================
        # MESSAGE FLASH
        # ====================================================

        message = request.session.pop(
            "message",
            None
        )

        # ====================================================
        # AFFICHAGE
        # ====================================================

        return templates.TemplateResponse(

            request=request,

            name="admin.html",

            context={

                "user":
                    admin,

                "users":
                    users,

                "products":
                    products,

                "boutiques":
                    boutiques,

                "boutique_requests":
                    boutique_requests,

                "contact_messages":
                    contact_messages,

                "orders":
                    orders,

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

                "pending_order_count":
                    pending_order_count,

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
# COMMANDES — PRENDRE EN CHARGE
# ============================================================

@router.post(
    "/admin/commande/livraison/{order_id}"
)
async def prendre_commande_en_charge(

    request: Request,

    order_id: int

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

        order = (
            db.query(Order)
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if not order:

            request.session["message"] = (
                "❌ Commande introuvable."
            )

            return admin_redirect()

        if order.delivery_status != "pending":

            request.session["message"] = (
                "⚠️ Cette commande n'est plus "
                "en attente de prise en charge."
            )

            return admin_redirect()

        order.delivery_status = "assigned"

        order.delivery_person = "Papa"

        db.commit()

        print(
            f"🚚 Commande #{order.order_number} "
            "prise en charge."
        )

        request.session["message"] = (
            f"🚚 Commande #{order.order_number} "
            "prise en charge."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR PRISE EN CHARGE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de prendre en charge "
            "la commande."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# COMMANDES — LIVRAISON EN COURS
# ============================================================

@router.post(
    "/admin/commande/livraison/en-cours/{order_id}"
)
async def livraison_en_cours(

    request: Request,

    order_id: int

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

        order = (
            db.query(Order)
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if not order:

            request.session["message"] = (
                "❌ Commande introuvable."
            )

            return admin_redirect()

        if order.delivery_status != "assigned":

            request.session["message"] = (
                "⚠️ La commande n'est pas "
                "prête pour la livraison."
            )

            return admin_redirect()

        order.delivery_status = "in_transit"

        order.status = "pending"

        order.delivery_person = "Papa"

        db.commit()

        print(
            f"🚚 Commande #{order.order_number} "
            "en cours de livraison."
        )

        request.session["message"] = (
            f"🚚 Commande #{order.order_number} "
            "est maintenant en cours de livraison."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR LIVRAISON EN COURS :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de modifier "
            "le statut de livraison."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# COMMANDES — ANNULER LA PRISE EN CHARGE
# ============================================================

@router.post(
    "/admin/commande/livraison/annuler/{order_id}"
)
async def annuler_prise_en_charge(

    request: Request,

    order_id: int

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

        order = (
            db.query(Order)
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if not order:

            request.session["message"] = (
                "❌ Commande introuvable."
            )

            return admin_redirect()

        if order.delivery_status != "assigned":

            request.session["message"] = (
                "⚠️ Cette commande ne peut "
                "plus être annulée à cette étape."
            )

            return admin_redirect()

        order.delivery_status = "pending"

        order.delivery_person = None

        db.commit()

        print(
            f"↩️ Prise en charge annulée "
            f"pour la commande #{order.order_number}."
        )

        request.session["message"] = (
            f"↩️ Prise en charge de la commande "
            f"#{order.order_number} annulée."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR ANNULATION LIVRAISON :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible d'annuler "
            "la prise en charge."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# COMMANDES — LIVRÉE / PAIEMENT REÇU
# ============================================================

@router.post(
    "/admin/commande/livraison/livree/{order_id}"
)
async def commande_livree(

    request: Request,

    order_id: int

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

        order = (
            db.query(Order)
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if not order:

            request.session["message"] = (
                "❌ Commande introuvable."
            )

            return admin_redirect()

        if order.delivery_status != "in_transit":

            request.session["message"] = (
                "⚠️ Cette commande n'est pas "
                "en cours de livraison."
            )

            return admin_redirect()

        order.delivery_status = "delivered"

        order.status = "completed"

        order.payment_status = "paid"

        order.delivery_person = "Papa"

        db.commit()

        print(
            f"✅ Commande #{order.order_number} "
            "livrée et paiement reçu."
        )

        request.session["message"] = (
            f"✅ Commande #{order.order_number} "
            "livrée. Paiement reçu."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR COMMANDE LIVRÉE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de terminer "
            "la commande."
        )

        return admin_redirect()

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

        if user_id == admin.id:

            request.session["message"] = (
                "❌ Vous ne pouvez pas supprimer "
                "votre propre compte administrateur."
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

        user_name = user.full_name

        orders = (
            db.query(Order)
            .filter(
                Order.user_id == user.id
            )
            .all()
        )

        order_count = len(orders)

        for order in orders:

            order.user_id = None

        products = (
            db.query(Product)
            .filter(
                Product.user_id == user.id
            )
            .all()
        )

        product_ids = [
            product.id
            for product in products
        ]

        order_item_count = 0

        if product_ids:

            order_items = (
                db.query(OrderItem)
                .filter(
                    OrderItem.product_id.in_(
                        product_ids
                    )
                )
                .all()
            )

            order_item_count = len(order_items)

            for order_item in order_items:

                order_item.product_id = None

        for product in products:

            db.delete(product)

        boutiques = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user.id
            )
            .all()
        )

        for boutique in boutiques:

            db.delete(boutique)

        requests_list = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.user_id == user.id
            )
            .all()
        )

        for boutique_request in requests_list:

            db.delete(
                boutique_request
            )

        db.delete(user)

        db.commit()

        request.session["message"] = (

            f"✅ Utilisateur « {user_name} » "
            "supprimé définitivement. "

            f"{order_count} commande(s) "
            "et leur historique ont été conservés."
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
            "cet utilisateur."
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


# ============================================================
# SUPPRIMER UNE ANNONCE
# ============================================================

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

        order_item_exists = (
            db.query(OrderItem)
            .filter(
                OrderItem.product_id == product.id
            )
            .first()
        )

        if order_item_exists:

            product.is_active = False

            db.commit()

            request.session["message"] = (
                f"⛔ Annonce « {product_title} » "
                "désactivée. Elle est conservée "
                "afin de préserver l'historique "
                "des commandes."
            )

            return admin_redirect()

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
            "❌ ERREUR SUPPRESSION ANNONCE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "cette annonce."
        )

        return admin_redirect()

    finally:

        db.close()


# ============================================================
# SUPPRESSION DÉFINITIVE ANNONCE
# ============================================================

@router.post(
    "/admin/annonce/supprimer-definitivement/{product_id}"
)
async def supprimer_annonce_definitivement(

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

        order_items = (
            db.query(OrderItem)
            .filter(
                OrderItem.product_id == product.id
            )
            .all()
        )

        order_count = len(order_items)

        for order_item in order_items:

            order_item.product_id = None

        db.delete(product)

        db.commit()

        request.session["message"] = (
            f"☠️ Annonce « {product_title} » "
            "supprimée définitivement. "
            f"{order_count} élément(s) de commande "
            "conservé(s)."
        )

        return admin_redirect()

    except Exception as e:

        db.rollback()

        print(
            "❌ ERREUR SUPPRESSION DÉFINITIVE :",
            repr(e)
        )

        request.session["message"] = (
            "❌ Impossible de supprimer "
            "définitivement cette annonce."
        )

        return admin_redirect()

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

        product.is_active = False

        db.commit()

        request.session["message"] = (
            f"⛔ Annonce « {product.title} » "
            "désactivée."
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

        products = (
            db.query(Product)
            .filter(
                Product.boutique_id == boutique.id
            )
            .all()
        )

        product_ids = [
            product.id
            for product in products
        ]

        if product_ids:

            order_items = (
                db.query(OrderItem)
                .filter(
                    OrderItem.product_id.in_(
                        product_ids
                    )
                )
                .all()
            )

            for order_item in order_items:

                order_item.product_id = None

        for product in products:

            db.delete(product)

        db.delete(boutique)

        db.commit()

        request.session["message"] = (
            f"🗑️ Boutique « {boutique_name} » "
            "et ses annonces ont été supprimées. "
            "L'historique des commandes "
            "a été conservé."
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