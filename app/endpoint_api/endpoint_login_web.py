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
    secure   = False,    # False en dev local (HTTP)
    samesite = "lax",
    max_age  = 60 * 60 * 24 * 7,   # 7 jours
)


@router.post(
    "/login/web",
    response_model=LoginWebResponse,
    summary="Connexion d'un utilisateur web",
    tags=["Auth"],
)
async def login_web(body: LoginWebRequest) -> JSONResponse:
    """
    Vérifie les credentials et pose 3 cookies HttpOnly :
      - session_user_id
      - session_identifiant
      - session_email
    """

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

    except Exception:
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

    # ── Pose des 3 cookies HttpOnly ──────────────────────
    response.set_cookie(key="session_user_id",    value=user.user_id,                **COOKIE_OPTS)
    response.set_cookie(key="session_identifiant", value=user.identifiant,            **COOKIE_OPTS)
    response.set_cookie(key="session_email",       value=user.email or "",            **COOKIE_OPTS)

    return response
