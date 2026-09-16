from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem

from app.translations.fr import TRANSLATIONS as FR
from app.translations.ar import TRANSLATIONS as AR

from datetime import datetime
import uuid


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =========================================================
# LANGUE
# =========================================================

def get_language(request: Request):
    lang = request.query_params.get("lang", "fr")

    if lang not in ["fr", "ar"]:
        lang = "fr"

    return lang


def get_translations(lang):
    if lang == "ar":
        return AR

    return FR


# =========================================================
# AJOUTER UN PRODUIT AU PANIER
# =========================================================

@router.post("/panier/ajouter/{product_id}")
async def ajouter_au_panier(
    request: Request,
    product_id: int
):
    lang = get_language(request)
    translations = get_translations(lang)

    db = SessionLocal()

    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )
    finally:
        db.close()

    # ---------------------------------------------------------
    # PRODUIT INTROUVABLE
    # ---------------------------------------------------------

    if not product:
        request.session["message"] = translations.get(
            "not_found",
            (
                "Produit introuvable."
                if lang == "fr"
                else "المنتج غير موجود."
            )
        )

        return RedirectResponse(
            url=f"/?lang={lang}",
            status_code=303
        )

    # ---------------------------------------------------------
    # RÉCUPÉRATION DU PANIER
    # ---------------------------------------------------------

    panier = request.session.get(
        "panier",
        []
    )

    if not isinstance(panier, list):
        panier = []

    # ---------------------------------------------------------
    # AJOUT DU PRODUIT
    # ---------------------------------------------------------

    if product_id not in panier:
        panier.append(product_id)

    request.session["panier"] = panier

    # ---------------------------------------------------------
    # MESSAGE SPÉCIFIQUE À L'AJOUT AU PANIER
    #
    # IMPORTANT :
    # On utilise une clé différente de "message".
    # Cela empêche le message d'apparaître dans /panier.
    # ---------------------------------------------------------

    request.session["product_added_message"] = translations.get(
        "product_added_to_cart",
        (
            "Produit ajouté au panier avec succès."
            if lang == "fr"
            else "تمت إضافة المنتج إلى السلة بنجاح."
        )
    )

    # ---------------------------------------------------------
    # RETOUR IMMÉDIAT SUR LA PAGE DU PRODUIT
    # ---------------------------------------------------------

    return RedirectResponse(
        url=f"/produit/{product_id}?lang={lang}",
        status_code=303
    )


# =========================================================
# AFFICHER LE PANIER
# =========================================================

@router.get("/panier")
async def afficher_panier(
    request: Request
):
    lang = get_language(request)
    translations = get_translations(lang)

    panier = request.session.get(
        "panier",
        []
    )

    if not isinstance(panier, list):
        panier = []

    # ---------------------------------------------------------
    # IMPORTANT :
    # Le message "produit ajouté" n'est PAS récupéré ici.
    #
    # Il est réservé à la page produit.
    # ---------------------------------------------------------

    message = request.session.pop(
        "message",
        None
    )

    db = SessionLocal()

    try:
        if panier:
            products = (
                db.query(Product)
                .filter(
                    Product.id.in_(panier)
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
            "total": total,
            "lang": lang,
            "t": translations,
            "message": message
        }
    )


# =========================================================
# SUPPRIMER UN PRODUIT DU PANIER
# =========================================================

@router.get("/panier/supprimer/{product_id}")
async def supprimer_du_panier(
    request: Request,
    product_id: int
):
    lang = get_language(request)

    panier = request.session.get(
        "panier",
        []
    )

    if not isinstance(panier, list):
        panier = []

    if product_id in panier:
        panier.remove(product_id)

    request.session["panier"] = panier

    return RedirectResponse(
        url=f"/panier?lang={lang}",
        status_code=303
    )


# =========================================================
# COMMANDER DIRECTEMENT UN PRODUIT
# =========================================================

@router.post("/commande/direct/{product_id}")
async def commander_directement(
    request: Request,
    product_id: int
):
    lang = get_language(request)
    translations = get_translations(lang)

    db = SessionLocal()

    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )
    finally:
        db.close()

    # ---------------------------------------------------------
    # PRODUIT INTROUVABLE
    # ---------------------------------------------------------

    if not product:
        request.session["message"] = translations.get(
            "not_found",
            (
                "Produit introuvable ou indisponible."
                if lang == "fr"
                else "المنتج غير موجود أو غير متاح."
            )
        )

        return RedirectResponse(
            url=f"/?lang={lang}",
            status_code=303
        )

    # ---------------------------------------------------------
    # REMPLACER LE PANIER PAR CE PRODUIT
    # ---------------------------------------------------------

    request.session["panier"] = [
        product_id
    ]

    return RedirectResponse(
        url=f"/commande?lang={lang}",
        status_code=303
    )


# =========================================================
# PAGE COMMANDE
# =========================================================

@router.get("/commande")
async def page_commande(
    request: Request
):
    lang = get_language(request)
    translations = get_translations(lang)

    panier = request.session.get(
        "panier",
        []
    )

    if not isinstance(panier, list):
        panier = []

    # ---------------------------------------------------------
    # MESSAGE NORMAL DE COMMANDE
    # ---------------------------------------------------------

    message = request.session.pop(
        "message",
        None
    )

    # ---------------------------------------------------------
    # PANIER VIDE
    # ---------------------------------------------------------

    if not panier:
        request.session["message"] = (
            "Votre panier est vide."
            if lang == "fr"
            else "سلتك فارغة."
        )

        return RedirectResponse(
            url=f"/panier?lang={lang}",
            status_code=303
        )

    db = SessionLocal()

    try:
        products = (
            db.query(Product)
            .filter(
                Product.id.in_(panier)
            )
            .all()
        )

        # -----------------------------------------------------
        # PRODUITS INDISPONIBLES
        # -----------------------------------------------------

        if not products:
            request.session["message"] = (
                "Les produits de votre panier "
                "ne sont plus disponibles."
                if lang == "fr"
                else "المنتجات الموجودة في سلتك "
                     "لم تعد متاحة."
            )

            return RedirectResponse(
                url=f"/panier?lang={lang}",
                status_code=303
            )

        # -----------------------------------------------------
        # TOTAL
        # -----------------------------------------------------

        total = sum(
            product.price or 0
            for product in products
        )

        # -----------------------------------------------------
        # UTILISATEUR
        # -----------------------------------------------------

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
                "user_name": user_name,
                "lang": lang,
                "t": translations,
                "message": message
            }
        )

    finally:
        db.close()


# =========================================================
# VALIDER LA COMMANDE
# =========================================================

@router.post("/commande/valider")
async def valider_commande(
    request: Request,
    customer_name: str = Form(""),
    customer_phone: str = Form(""),
    city: str = Form(""),
    delivery_address: str = Form(""),
    comment: str = Form("")
):
    lang = get_language(request)

    panier = request.session.get(
        "panier",
        []
    )

    if not isinstance(panier, list):
        panier = []

    # ---------------------------------------------------------
    # PANIER VIDE
    # ---------------------------------------------------------

    if not panier:
        request.session["message"] = (
            "Votre panier est vide."
            if lang == "fr"
            else "سلتك فارغة."
        )

        return RedirectResponse(
            url=f"/panier?lang={lang}",
            status_code=303
        )

    # ---------------------------------------------------------
    # NETTOYAGE DES CHAMPS
    # ---------------------------------------------------------

    customer_name = customer_name.strip()
    customer_phone = customer_phone.strip()
    city = city.strip()
    delivery_address = delivery_address.strip()
    comment = comment.strip()

    # ---------------------------------------------------------
    # CHAMPS OBLIGATOIRES
    # ---------------------------------------------------------

    if not customer_name or not customer_phone or not city:
        request.session["message"] = (
            "Veuillez remplir les champs obligatoires."
            if lang == "fr"
            else "يرجى ملء الحقول المطلوبة."
        )

        return RedirectResponse(
            url=f"/commande?lang={lang}",
            status_code=303
        )

    db = SessionLocal()

    try:
        # -----------------------------------------------------
        # PRODUITS DU PANIER
        # -----------------------------------------------------

        products = (
            db.query(Product)
            .filter(
                Product.id.in_(panier)
            )
            .all()
        )

        if not products:
            request.session["message"] = (
                "Aucun produit disponible."
                if lang == "fr"
                else "لا يوجد أي منتج متاح."
            )

            return RedirectResponse(
                url=f"/panier?lang={lang}",
                status_code=303
            )

        # -----------------------------------------------------
        # TOTAL
        # -----------------------------------------------------

        total = sum(
            product.price or 0
            for product in products
        )

        # -----------------------------------------------------
        # UTILISATEUR
        # -----------------------------------------------------

        user_id = request.session.get(
            "user_id"
        )

        # -----------------------------------------------------
        # NUMÉRO DE COMMANDE
        # -----------------------------------------------------

        order_number = (
            "MM-"
            + datetime.now().strftime("%Y%m%d")
            + "-"
            + uuid.uuid4().hex[:6].upper()
        )

        # -----------------------------------------------------
        # CRÉATION DE LA COMMANDE
        # -----------------------------------------------------

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
            payment_method="manuel"
        )

        db.add(order)

        db.flush()

        # -----------------------------------------------------
        # ARTICLES DE LA COMMANDE
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # ENREGISTREMENT
        # -----------------------------------------------------

        db.commit()

        db.refresh(order)

        # -----------------------------------------------------
        # NETTOYAGE DU PANIER
        # -----------------------------------------------------

        request.session["panier"] = []

        request.session["commande_id"] = order.id

        request.session["commande_number"] = (
            order.order_number
        )

        return RedirectResponse(
            url=f"/commande/succes/{order.id}?lang={lang}",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "=========================================="
        )

        print(
            "ERREUR CREATION COMMANDE :",
            repr(e)
        )

        print(
            "=========================================="
        )

        request.session["message"] = (
            "Impossible d'enregistrer "
            "la commande pour le moment."
            if lang == "fr"
            else "تعذر تسجيل الطلب في الوقت الحالي."
        )

        return RedirectResponse(
            url=f"/commande?lang={lang}",
            status_code=303
        )

    finally:
        db.close()


# =========================================================
# SUCCÈS DE LA COMMANDE
# =========================================================

@router.get("/commande/succes/{order_id}")
async def commande_succes(
    request: Request,
    order_id: int
):
    lang = get_language(request)
    translations = get_translations(lang)

    db = SessionLocal()

    try:

        # -----------------------------------------------------
        # COMMANDE
        # -----------------------------------------------------

        order = (
            db.query(Order)
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if not order:
            return RedirectResponse(
                url=f"/?lang={lang}",
                status_code=303
            )

        # -----------------------------------------------------
        # ARTICLES
        # -----------------------------------------------------

        items = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order.id
            )
            .all()
        )

        # -----------------------------------------------------
        # MESSAGE
        # -----------------------------------------------------

        message = request.session.pop(
            "message",
            None
        )

        return templates.TemplateResponse(
            request=request,
            name="commande_succes.html",
            context={
                "order": order,
                "items": items,
                "lang": lang,
                "t": translations,
                "message": message
            }
        )

    finally:
        db.close()
