# ================================================
# endpoint_login_web.py
# Endpoint POST /login/web
# Vérifie les credentials et pose les cookies HttpOnly
# ================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.base_model_login_web import LoginWebRequest, LoginWebResponse
from app.request_command.login.verif_login_web import verify_login

router = APIRouter()

COOKIE_OPTS = dict(
    httponly = True,
    secure   = False,
    samesite = "lax",
    max_age  = 60 * 60 * 24 * 7,
)


@router.post(
    "/login/web",
    response_model=LoginWebResponse,
    summary="Connexion d'un utilisateur web",
    tags=["Auth"],
)
async def login_web(body: LoginWebRequest) -> JSONResponse:

    try:
        user = verify_login(body)

    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content=LoginWebResponse(
                success=False,
                message=str(e),
            ).model_dump(),
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[DEBUG] ❌ Exception : {type(e).__name__} — {e}")
        return JSONResponse(
            status_code=500,
            content=LoginWebResponse(
                success=False,
                message="Une erreur interne est survenue. Veuillez réessayer.",
            ).model_dump(),
        )

    response = JSONResponse(
        status_code=200,
        content=LoginWebResponse(
            success=True,
            message="Connexion réussie.",
            user_id=user.user_id,
        ).model_dump(),
    )

    # ── Pose des cookies HttpOnly ──────────────────────
    response.set_cookie(key="session_user_id",     value=user.user_id,        **COOKIE_OPTS)
    response.set_cookie(key="session_identifiant", value=user.identifiant,     **COOKIE_OPTS)
    response.set_cookie(key="session_email",       value=user.email or "",     **COOKIE_OPTS)
    response.set_cookie(key="session_nom",         value=user.nom    or "",    **COOKIE_OPTS)
    response.set_cookie(key="session_prenom",      value=user.prenom or "",    **COOKIE_OPTS)

    return response