from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import joinedload

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem

from datetime import datetime
import uuid


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# AJOUTER AU PANIER
# =====================================================

@router.post("/panier/ajouter/{product_id}")
async def ajouter_au_panier(
    request: Request,
    product_id: int
):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id,
                Product.is_active == True
            )
            .first()
        )

    finally:

        db.close()

    if not product:

        request.session["message"] = (
            "Produit introuvable ou indisponible."
        )

        return RedirectResponse(
            url="/",
            status_code=303
        )

    panier = request.session.get(
        "panier",
        []
    )

    if product_id not in panier:

        panier.append(product_id)

    request.session["panier"] = panier

    request.session["message"] = (
        "Produit ajouté au panier."
    )

    return RedirectResponse(
        url=f"/produit/{product_id}",
        status_code=303
    )


# =====================================================
# AFFICHER LE PANIER
# =====================================================

@router.get("/panier")
async def afficher_panier(
    request: Request
):

    panier = request.session.get(
        "panier",
        []
    )

    db = SessionLocal()

    try:

        if panier:

            products = (
                db.query(Product)
                .filter(
                    Product.id.in_(panier),
                    Product.is_active == True
                )
                .all()
            )

        else:

            products = []

        total = sum(
            product.price or 0
            for product in products
        )

    finally:

        db.close()

    return templates.TemplateResponse(
        request=request,
        name="panier.html",
        context={
            "products": products,
            "total": total
        }
    )


# =====================================================
# SUPPRIMER DU PANIER
# =====================================================

@router.get("/panier/supprimer/{product_id}")
async def supprimer_du_panier(
    request: Request,
    product_id: int
):

    panier = request.session.get(
        "panier",
        []
    )

    if product_id in panier:

        panier.remove(product_id)

    request.session["panier"] = panier

    return RedirectResponse(
        url="/panier",
        status_code=303
    )


# =====================================================
# PAGE VALIDATION DE COMMANDE
# =====================================================

# =====================================================
# COMMANDER DIRECTEMENT UN PRODUIT
# =====================================================

@router.post("/commande/direct/{product_id}")
async def commander_directement(
    request: Request,
    product_id: int
):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id,
                Product.is_active == True
            )
            .first()
        )

    finally:

        db.close()

    if not product:

        request.session["message"] = (
            "Produit introuvable ou indisponible."
        )

        return RedirectResponse(
            url="/",
            status_code=303
        )

    request.session["panier"] = [product_id]

    return RedirectResponse(
        url="/commande",
        status_code=303
    )

@router.get("/commande")
async def page_commande(
    request: Request
):

    panier = request.session.get(
        "panier",
        []
    )

    if not panier:

        request.session["message"] = (
            "Votre panier est vide."
        )

        return RedirectResponse(
            url="/panier",
            status_code=303
        )

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .filter(
                Product.id.in_(panier),
                Product.is_active == True
            )
            .all()
        )

        if not products:

            request.session["message"] = (
                "Les produits de votre panier "
                "ne sont plus disponibles."
            )

            return RedirectResponse(
                url="/panier",
                status_code=303
            )

        total = sum(
            product.price or 0
            for product in products
        )

        user_id = request.session.get(
            "user_id"
        )

        user_name = request.session.get(
            "user_name",
            ""
        )

        return templates.TemplateResponse(
            request=request,
            name="commande.html",
            context={
                "products": products,
                "total": total,
                "user_id": user_id,
                "user_name": user_name
            }
        )

    finally:

        db.close()


# =====================================================
# VALIDER LA COMMANDE
#
# LIVRAISON MANUELLE
#
# Le fonctionnement est volontairement simple :
#
# - Le client passe la commande.
# - La commande est enregistrée.
# - Le livreur est automatiquement "Papa".
# - Le statut livraison commence à "pending".
# - Le vendeur peut être contacté.
# - Papa récupère le produit.
# - Papa livre le client.
# - Le client paie à la livraison.
# =====================================================

@router.post("/commande/valider")
async def valider_commande(
    request: Request,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    city: str = Form(...),
    delivery_address: str = Form(""),
    comment: str = Form("")
):

    panier = request.session.get(
        "panier",
        []
    )

    if not panier:

        request.session["message"] = (
            "Votre panier est vide."
        )

        return RedirectResponse(
            url="/panier",
            status_code=303
        )

    # -------------------------------------------------
    # NETTOYAGE DES INFORMATIONS
    # -------------------------------------------------

    customer_name = customer_name.strip()
    customer_phone = customer_phone.strip()
    city = city.strip()
    delivery_address = delivery_address.strip()
    comment = comment.strip()

    # -------------------------------------------------
    # VÉRIFICATION
    # -------------------------------------------------

    if (
        not customer_name
        or not customer_phone
        or not city
    ):

        request.session["message"] = (
            "Veuillez remplir les champs obligatoires."
        )

        return RedirectResponse(
            url="/commande",
            status_code=303
        )

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # RÉCUPÉRER LES PRODUITS
        # -------------------------------------------------

        products = (
            db.query(Product)
            .filter(
                Product.id.in_(panier),
                Product.is_active == True
            )
            .all()
        )

        if not products:

            request.session["message"] = (
                "Aucun produit disponible."
            )

            return RedirectResponse(
                url="/panier",
                status_code=303
            )

        # -------------------------------------------------
        # TOTAL
        # -------------------------------------------------

        total = sum(
            product.price or 0
            for product in products
        )

        # -------------------------------------------------
        # UTILISATEUR CONNECTÉ
        # -------------------------------------------------

        user_id = request.session.get(
            "user_id"
        )

        # -------------------------------------------------
        # NUMÉRO DE COMMANDE
        # -------------------------------------------------

        order_number = (
            "MM-"
            + datetime.now().strftime("%Y%m%d")
            + "-"
            + uuid.uuid4().hex[:6].upper()
        )

        # -------------------------------------------------
        # CRÉATION DE LA COMMANDE
        #
        # LIVRAISON :
        #
        # delivery_status = pending
        # delivery_person = Papa
        #
        # PAIEMENT :
        #
        # payment_method = manuel
        # payment_status = pending
        # -------------------------------------------------

        order = Order(

            order_number=order_number,

            user_id=user_id,

            customer_name=customer_name,

            customer_phone=customer_phone,

            city=city,

            delivery_address=(
                delivery_address
                or None
            ),

            comment=(
                comment
                or None
            ),

            total=total,

            status="pending",

            payment_status="pending",

            payment_method="manuel",

            delivery_status="pending",

            delivery_person="Papa"
        )

        db.add(order)

        db.flush()

        # -------------------------------------------------
        # AJOUT DES PRODUITS À LA COMMANDE
        # -------------------------------------------------

        for product in products:

            price = product.price or 0

            order_item = OrderItem(

                order_id=order.id,

                product_id=product.id,

                product_title=product.title,

                price=price,

                quantity=1,

                subtotal=price
            )

            db.add(order_item)

        # -------------------------------------------------
        # ENREGISTRER
        # -------------------------------------------------

        db.commit()

        db.refresh(order)

        # -------------------------------------------------
        # VIDER LE PANIER
        # -------------------------------------------------

        request.session["panier"] = []

        # -------------------------------------------------
        # MÉMORISER LA COMMANDE
        # -------------------------------------------------

        request.session["commande_id"] = (
            order.id
        )

        request.session["commande_number"] = (
            order.order_number
        )

        # -------------------------------------------------
        # REDIRECTION
        # -------------------------------------------------

        return RedirectResponse(
            url=f"/commande/succes/{order.id}",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "=========================================="
        )

        print(
            "❌ ERREUR CREATION COMMANDE :",
            repr(e)
        )

        print(
            "=========================================="
        )

        request.session["message"] = (
            "Impossible d'enregistrer "
            "la commande pour le moment."
        )

        return RedirectResponse(
            url="/commande",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# COMMANDE ENREGISTRÉE
# =====================================================

@router.get("/commande/succes/{order_id}")
async def commande_succes(
    request: Request,
    order_id: int
):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # RÉCUPÉRER LA COMMANDE
        # -------------------------------------------------

        order = (
            db.query(Order)
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if not order:

            return RedirectResponse(
                url="/",
                status_code=303
            )

        # -------------------------------------------------
        # RÉCUPÉRER LES ARTICLES
        # -------------------------------------------------

        items = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order.id
            )
            .all()
        )

        # -------------------------------------------------
        # AFFICHER
        # -------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="commande_succes.html",
            context={
                "order": order,
                "items": items
            }
        )

    finally:

        db.close()

