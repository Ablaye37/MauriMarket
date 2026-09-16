from uuid import uuid4
from urllib.parse import urlparse, unquote
import os
import traceback

from fastapi import (
    APIRouter,
    Request,
    Depends,
    UploadFile,
    File,
    Form,
)

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.boutique import Boutique
from app.models.boutique_request import BoutiqueRequest
from app.models.product import Product
from app.models.user import User

from app.translations.fr import TRANSLATIONS as FR
from app.translations.ar import TRANSLATIONS as AR

from supabase import create_client


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# TEMPLATES
# ============================================================

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# CONFIGURATION SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SUPABASE_BUCKET = "product-images"


supabase = None


if SUPABASE_URL and SUPABASE_KEY:

    try:

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        print(
            "✅ Client Supabase initialisé"
        )

        print(
            "✅ Bucket images :",
            SUPABASE_BUCKET
        )

    except Exception as e:

        print(
            "❌ ERREUR INITIALISATION SUPABASE :",
            repr(e)
        )

else:

    print(
        "❌ SUPABASE_URL ou SUPABASE_KEY manquant."
    )


# ============================================================
# TYPES D'IMAGES AUTORISÉS
# ============================================================

ALLOWED_IMAGE_TYPES = {

    "image/jpeg": ".jpg",

    "image/png": ".png",

    "image/webp": ".webp",
}


# ============================================================
# DATABASE
# ============================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


# ============================================================
# LANGUE
# ============================================================

def get_language(request: Request):

    lang = request.query_params.get(
        "lang",
        "fr"
    )

    if lang not in ["fr", "ar"]:

        lang = "fr"

    translations = (
        FR
        if lang == "fr"
        else AR
    )

    return lang, translations


# ============================================================
# UTILISATEUR CONNECTÉ / SESSION VALIDE
# ============================================================

def get_current_user(
    request: Request,
    db: Session
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return None

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        request.session.clear()

        request.session["message"] = (
            "Votre session n'est plus valide. "
            "Veuillez vous reconnecter."
        )

        print(
            "⚠️ SESSION NETTOYÉE : user_id inexistant :",
            user_id
        )

        return None

    return user


# ============================================================
# CONTEXTE GLOBAL
# ============================================================

def contexte_global(
    request: Request,
    db: Session
):

    user_id = request.session.get(
        "user_id"
    )

    user_name = request.session.get(
        "user_name"
    )

    has_boutique = False

    boutique_request = None

    # --------------------------------------------------------
    # LANGUE
    # --------------------------------------------------------

    lang, translations = get_language(
        request
    )

    # --------------------------------------------------------
    # UTILISATEUR CONNECTÉ
    # --------------------------------------------------------

    if user_id:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:

            request.session.clear()

            request.session["message"] = (
                translations["server_error"]
            )

            user_id = None
            user_name = None

        else:

            user_name = user.full_name

    # --------------------------------------------------------
    # BOUTIQUE UTILISATEUR
    # --------------------------------------------------------

    if user_id:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        has_boutique = (
            boutique is not None
        )

        # ----------------------------------------------------
        # DERNIÈRE DEMANDE DE BOUTIQUE
        # ----------------------------------------------------

        boutique_request = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.user_id == user_id
            )
            .order_by(
                BoutiqueRequest.id.desc()
            )
            .first()
        )

    # --------------------------------------------------------
    # PANIER
    # --------------------------------------------------------

    panier = request.session.get(
        "panier",
        []
    )

    panier_count = len(
        panier
    )

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    return {

        "user_id":
            user_id,

        "user_name":
            user_name,

        "has_boutique":
            has_boutique,

        "boutique_request":
            boutique_request,

        "panier_count":
            panier_count,

        "lang":
            lang,

        "t":
            translations,
    }


# ============================================================
# UPLOAD IMAGE SUR SUPABASE
# ============================================================

async def upload_boutique_image(
    image: UploadFile,
    prefix: str,
):

    if not image or not image.filename:

        print(
            "ℹ️ Aucun fichier image fourni."
        )

        return None

    if not supabase:

        print(
            "❌ Supabase n'est pas configuré."
        )

        return None

    extension = ALLOWED_IMAGE_TYPES.get(
        image.content_type
    )

    if not extension:

        print(
            "❌ Type d'image non autorisé :",
            image.content_type
        )

        return None

    content = await image.read()

    if not content:

        print(
            "❌ Image vide."
        )

        return None

    filename = (
        f"{prefix}_"
        f"{uuid4().hex}"
        f"{extension}"
    )

    try:

        supabase.storage \
            .from_(SUPABASE_BUCKET) \
            .upload(

                path=filename,

                file=content,

                file_options={

                    "content-type":
                        image.content_type,

                    "cache-control":
                        "3600",

                    "upsert":
                        "false",
                }
            )

        print(
            "=========================================="
        )

        print(
            "✅ IMAGE ENVOYÉE SUR SUPABASE"
        )

        print(
            "BUCKET :",
            SUPABASE_BUCKET
        )

        print(
            "FICHIER :",
            filename
        )

        print(
            "=========================================="
        )

    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "❌ ERREUR UPLOAD SUPABASE"
        )

        print(
            "TYPE :",
            type(e).__name__
        )

        print(
            "ERREUR :",
            str(e)
        )

        traceback.print_exc()

        print(
            "=========================================="
        )

        return None

    try:

        public_url = (
            supabase
            .storage
            .from_(SUPABASE_BUCKET)
            .get_public_url(
                filename
            )
        )

        print(
            "✅ URL SUPABASE :",
            public_url
        )

        return public_url

    except Exception as e:

        print(
            "❌ ERREUR RÉCUPÉRATION URL :",
            repr(e)
        )

        return None


# ============================================================
# SUPPRIMER UNE IMAGE SUPABASE
# ============================================================

def delete_supabase_image(
    image_url: str | None
):

    if not image_url:
        return

    if not supabase:
        return

    if "supabase.co/storage/v1/object/" not in image_url:

        print(
            "ℹ️ Ancienne image locale détectée :",
            image_url
        )

        return

    try:

        parsed = urlparse(
            image_url
        )

        path = unquote(
            parsed.path
        )

        marker = (
            f"/storage/v1/object/public/"
            f"{SUPABASE_BUCKET}/"
        )

        if marker not in path:

            print(
                "ℹ️ Image Supabase provenant d'un autre bucket."
            )

            return

        file_path = path.split(
            marker,
            1
        )[1]

        if not file_path:
            return

        supabase.storage \
            .from_(SUPABASE_BUCKET) \
            .remove([
                file_path
            ])

        print(
            "✅ IMAGE SUPPRIMÉE DE SUPABASE :",
            file_path
        )

    except Exception as e:

        print(
            "⚠️ Impossible de supprimer l'image Supabase :",
            repr(e)
        )


# ============================================================
# BOUTIQUES
# ============================================================

@router.get("/boutiques")
async def boutiques(

    request: Request,

    q: str = "",

    db: Session = Depends(get_db),
):

    query = db.query(
        Boutique
    )

    # --------------------------------------------------------
    # RECHERCHE
    # --------------------------------------------------------

    if q:

        search = f"%{q}%"

        query = query.filter(

            (Boutique.name.ilike(search))
            |
            (Boutique.category.ilike(search))
            |
            (Boutique.sale_type.ilike(search))
            |
            (Boutique.city.ilike(search))
        )

    # --------------------------------------------------------
    # RÉCUPÉRATION
    # --------------------------------------------------------

    boutiques_list = (
        query
        .order_by(
            Boutique.id.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    context = contexte_global(
        request,
        db
    )

    context.update({

        "request":
            request,

        "boutiques":
            boutiques_list,

        "q":
            q,
    })

    return templates.TemplateResponse(

        request=request,

        name="boutiques.html",

        context=context,
    )


# ============================================================
# CRÉER UNE BOUTIQUE — PAGE
# ============================================================

@router.get("/boutique/creer")
async def page_creer_boutique(

    request: Request,

    db: Session = Depends(get_db),
):

    user = get_current_user(
        request,
        db
    )

    user_id = (
        user.id
        if user
        else None
    )

    lang, _ = get_language(
        request
    )

    if not user_id:

        return RedirectResponse(
            url=f"/login?lang={lang}",
            status_code=303,
        )

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if boutique:

        return RedirectResponse(
            url=f"/ma-boutique?lang={lang}",
            status_code=303,
        )

    demande = (
        db.query(BoutiqueRequest)
        .filter(
            BoutiqueRequest.user_id == user_id
        )
        .order_by(
            BoutiqueRequest.id.desc()
        )
        .first()
    )

    if demande and demande.status == "pending":

        return RedirectResponse(
            url=f"/boutique/demande?lang={lang}",
            status_code=303,
        )

    if demande and demande.status == "approved":

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        if not boutique:

            boutique = Boutique(

                name=demande.name,

                category=demande.category,

                sale_type=demande.sale_type,

                user_id=user_id,
            )

            db.add(
                boutique
            )

            db.commit()

            db.refresh(
                boutique
            )

        return RedirectResponse(
            url=f"/ma-boutique?lang={lang}",
            status_code=303,
        )

    context = contexte_global(
        request,
        db
    )

    context["request"] = request

    return templates.TemplateResponse(

        request=request,

        name="creer_boutique.html",

        context=context,
    )


# ============================================================
# CRÉER UNE DEMANDE DE BOUTIQUE
# ============================================================

@router.post("/boutique/creer")
async def creer_boutique(

    request: Request,

    name: str = Form(...),

    category: str = Form(""),

    sale_type: str = Form(""),

    db: Session = Depends(get_db),
):

    lang, translations = get_language(
        request
    )

    user = get_current_user(
        request,
        db
    )

    user_id = (
        user.id
        if user
        else None
    )

    if not user_id:

        return RedirectResponse(
            url=f"/login?lang={lang}",
            status_code=303,
        )

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if boutique:

        return RedirectResponse(
            url=f"/ma-boutique?lang={lang}",
            status_code=303,
        )

    derniere_demande = (
        db.query(BoutiqueRequest)
        .filter(
            BoutiqueRequest.user_id == user_id
        )
        .order_by(
            BoutiqueRequest.id.desc()
        )
        .first()
    )

    if (
        derniere_demande
        and derniere_demande.status == "pending"
    ):

        return RedirectResponse(
            url=f"/boutique/demande?lang={lang}",
            status_code=303,
        )

    if (
        derniere_demande
        and derniere_demande.status == "approved"
    ):

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        if not boutique:

            boutique = Boutique(

                name=derniere_demande.name,

                category=derniere_demande.category,

                sale_type=derniere_demande.sale_type,

                user_id=user_id,
            )

            db.add(
                boutique
            )

            db.commit()

            db.refresh(
                boutique
            )

        return RedirectResponse(
            url=f"/ma-boutique?lang={lang}",
            status_code=303,
        )

    demande = BoutiqueRequest(

        name=name.strip(),

        category=category.strip(),

        sale_type=sale_type.strip(),

        user_id=user_id,

        status="pending",
    )

    db.add(
        demande
    )

    db.commit()

    request.session["message"] = (
        translations.get(
            "shop_request_sent",
            "Votre demande de boutique a été envoyée."
        )
    )

    return RedirectResponse(
        url=f"/boutique/demande?lang={lang}",
        status_code=303,
    )


# ============================================================
# STATUT DE LA DEMANDE
# ============================================================

@router.get("/boutique/demande")
async def statut_demande(

    request: Request,

    db: Session = Depends(get_db),
):

    lang, _ = get_language(
        request
    )

    user = get_current_user(
        request,
        db
    )

    user_id = (
        user.id
        if user
        else None
    )

    if not user_id:

        return RedirectResponse(
            url=f"/login?lang={lang}",
            status_code=303,
        )

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if boutique:

        return RedirectResponse(
            url=f"/ma-boutique?lang={lang}",
            status_code=303,
        )

    demande = (
        db.query(BoutiqueRequest)
        .filter(
            BoutiqueRequest.user_id == user_id
        )
        .order_by(
            BoutiqueRequest.id.desc()
        )
        .first()
    )

    if demande and demande.status == "approved":

        boutique = Boutique(

            name=demande.name,

            category=demande.category,

            sale_type=demande.sale_type,

            user_id=user_id,
        )

        db.add(
            boutique
        )

        db.commit()

        return RedirectResponse(
            url=f"/ma-boutique?lang={lang}",
            status_code=303,
        )

    context = contexte_global(
        request,
        db
    )

    context.update({

        "request":
            request,

        "demande":
            demande,
    })

    return templates.TemplateResponse(

        request=request,

        name="publier_boutique.html",

        context=context,
    )


# ============================================================
# MA BOUTIQUE
# ============================================================

@router.get("/ma-boutique")
async def ma_boutique(

    request: Request,

    db: Session = Depends(get_db),

):

    lang, _ = get_language(
        request
    )

    user = get_current_user(
        request,
        db
    )

    user_id = (
        user.id
        if user
        else None
    )

    if not user_id:

        return RedirectResponse(
            url=f"/login?lang={lang}",
            status_code=303,
        )

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if not boutique:

        return RedirectResponse(
            url=f"/boutique/creer?lang={lang}",
            status_code=303,
        )

    products = (
        db.query(Product)
        .filter(
            Product.boutique_id == boutique.id,
            Product.is_active == True
        )
        .order_by(
            Product.id.desc()
        )
        .all()
    )

    context = contexte_global(
        request,
        db
    )

    context.update({

        "request":
            request,

        "boutique":
            boutique,

        "products":
            products,
    })

    return templates.TemplateResponse(

        request=request,

        name="ma_boutique.html",

        context=context,
    )


# ============================================================
# MODIFIER MA BOUTIQUE — PAGE
# ============================================================

@router.get("/ma-boutique/modifier")
async def page_modifier_boutique(

    request: Request,

    db: Session = Depends(get_db),

):

    lang, _ = get_language(
        request
    )

    user = get_current_user(
        request,
        db
    )

    user_id = (
        user.id
        if user
        else None
    )

    if not user_id:

        return RedirectResponse(
            url=f"/login?lang={lang}",
            status_code=303,
        )

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if not boutique:

        return RedirectResponse(
            url=f"/boutique/creer?lang={lang}",
            status_code=303,
        )

    context = contexte_global(
        request,
        db
    )

    context.update({

        "request":
            request,

        "boutique":
            boutique,
    })

    return templates.TemplateResponse(

        request=request,

        name="modifier_boutique.html",

        context=context,
    )


# ============================================================
# MODIFIER MA BOUTIQUE
# ============================================================

@router.post("/ma-boutique/modifier")
async def modifier_boutique(

    request: Request,

    name: str = Form(...),

    category: str = Form(""),

    sale_type: str = Form(""),

    description: str = Form(""),

    city: str = Form(""),

    logo: UploadFile | None = File(None),

    cover_image: UploadFile | None = File(None),

    db: Session = Depends(get_db),

):

    lang, _ = get_language(
        request
    )

    user = get_current_user(
        request,
        db
    )

    user_id = (
        user.id
        if user
        else None
    )

    if not user_id:

        return RedirectResponse(
            url=f"/login?lang={lang}",
            status_code=303,
        )

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if not boutique:

        return RedirectResponse(
            url=f"/boutique/creer?lang={lang}",
            status_code=303,
        )

    boutique.name = name.strip()

    boutique.category = category.strip()

    boutique.sale_type = sale_type.strip()

    boutique.description = description.strip()

    boutique.city = city.strip()

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    if logo and logo.filename:

        old_logo = boutique.logo

        logo_url = await upload_boutique_image(

            logo,

            f"boutique_{boutique.id}_logo"
        )

        if logo_url:

            boutique.logo = logo_url

            delete_supabase_image(
                old_logo
            )

    # --------------------------------------------------------
    # COUVERTURE
    # --------------------------------------------------------

    if cover_image and cover_image.filename:

        old_cover = boutique.cover_image

        cover_url = await upload_boutique_image(

            cover_image,

            f"boutique_{boutique.id}_cover"
        )

        if cover_url:

            boutique.cover_image = cover_url

            delete_supabase_image(
                old_cover
            )

    # --------------------------------------------------------
    # SAUVEGARDER
    # --------------------------------------------------------

    db.commit()

    db.refresh(
        boutique
    )

    request.session["message"] = (
        "Votre boutique a été modifiée avec succès."
    )

    print(
        "=========================================="
    )

    print(
        "✅ BOUTIQUE MODIFIÉE"
    )

    print(
        "BOUTIQUE ID :",
        boutique.id
    )

    print(
        "LOGO :",
        boutique.logo
    )

    print(
        "COUVERTURE :",
        boutique.cover_image
    )

    print(
        "=========================================="
    )

    return RedirectResponse(
        url=f"/ma-boutique?lang={lang}",
        status_code=303,
    )


# ============================================================
# DÉTAIL D'UNE BOUTIQUE
# ============================================================

@router.get(
    "/boutique/detail/{boutique_id}"
)
async def boutique_detail(

    boutique_id: int,

    request: Request,

    db: Session = Depends(get_db),

):

    lang, _ = get_language(
        request
    )

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.id == boutique_id
        )
        .first()
    )

    if not boutique:

        return RedirectResponse(
            url=f"/boutiques?lang={lang}",
            status_code=303,
        )

    products = (
        db.query(Product)
        .filter(
            Product.boutique_id == boutique.id,
            Product.is_active == True
        )
        .order_by(
            Product.id.desc()
        )
        .all()
    )

    context = contexte_global(
        request,
        db
    )

    context.update({

        "request":
            request,

        "boutique":
            boutique,

        "products":
            products,

        "produits":
            products,
    })

    return templates.TemplateResponse(

        request=request,

        name="boutique_detail.html",

        context=context,
    )


# ============================================================
# COMPATIBILITÉ AVEC L'ANCIEN LIEN
# ============================================================

@router.get(
    "/boutique/{boutique_id}"
)
async def boutique_detail_ancien_lien(

    boutique_id: int,

    request: Request,

    db: Session = Depends(get_db),

):

    return await boutique_detail(

        boutique_id=boutique_id,

        request=request,

        db=db,
    )
