# ================================================
# endpoint_login_web.py
# Endpoint POST /login/web
# Vérifie les credentials et pose les cookies HttpOnly
# ================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
from app.models.base_model_login_web import LoginWebRequest, LoginWebResponse
from app.request_command.login.verif_login_web import verify_login
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# ── Credentials admin depuis .env ─────────────────────────────────────────────
ADMIN_IDENTIFER  = os.getenv("ADMIN_IDENTIFER",  "")
PASSWORD_ADMIN   = os.getenv("PASSWORD_ADMIN",   "")

COOKIE_OPTS = dict(
    httponly = True,
    secure   = False,
    samesite = "lax",
    max_age  = 60 * 60 * 24 * 7,
)


@router.post(
    "/login/web",
    summary="Connexion d'un utilisateur web",
    tags=["Auth"],
)
async def login_web(body: LoginWebRequest) -> JSONResponse:

    # ── Vérifie si c'est l'admin ──────────────────────
    is_admin = (
        body.identifiant.strip() == ADMIN_IDENTIFER
        and body.mot_de_passe    == PASSWORD_ADMIN
        and ADMIN_IDENTIFER != ""
    )

    if is_admin:
        response = JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Connexion admin réussie.",
                "role":    "admin",
            },
        )
        response.set_cookie(key="session_user_id",     value="admin",           **COOKIE_OPTS)
        response.set_cookie(key="session_identifiant", value=ADMIN_IDENTIFER,   **COOKIE_OPTS)
        response.set_cookie(key="session_email",       value="",                **COOKIE_OPTS)
        response.set_cookie(key="session_nom",         value="Admin",           **COOKIE_OPTS)
        response.set_cookie(key="session_prenom",      value="",                **COOKIE_OPTS)
        response.set_cookie(key="session_role",        value="admin",           **COOKIE_OPTS)
        return response

    # ── Connexion utilisateur normal ──────────────────
    try:
        user = verify_login(body)

    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": str(e), "role": "user"},
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Une erreur interne est survenue.", "role": "user"},
        )

    response = JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Connexion réussie.",
            "user_id": user.user_id,
            "role":    "user",
        },
    )

    response.set_cookie(key="session_user_id",     value=user.user_id,        **COOKIE_OPTS)
    response.set_cookie(key="session_identifiant", value=user.identifiant,     **COOKIE_OPTS)
    response.set_cookie(key="session_email",       value=user.email or "",     **COOKIE_OPTS)
    response.set_cookie(key="session_nom",         value=user.nom    or "",    **COOKIE_OPTS)
    response.set_cookie(key="session_prenom",      value=user.prenom or "",    **COOKIE_OPTS)
    response.set_cookie(key="session_role",        value="user",               **COOKIE_OPTS)

    return response