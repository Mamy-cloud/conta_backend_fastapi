# ================================================
# sign_up_web.py
# Endpoint POST /sign_up/web
# Inscrit l'utilisateur et pose les cookies HttpOnly
# ================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.base_model_sign_up_web import SignUpWebRequest, SignUpWebResponse
from app.request_command.sign_up.update_table_sign_up_web import insert_new_user

router = APIRouter()

COOKIE_OPTS = dict(
    httponly = True,
    secure   = True,
    samesite = "lax",
    max_age  = 60 * 60 * 24 * 7,
)


@router.post(
    "/sign_up/web",
    response_model=SignUpWebResponse,
    summary="Inscription d'un nouvel utilisateur web",
    tags=["Auth"],
)
async def sign_up_web(body: SignUpWebRequest) -> JSONResponse:

    print("=" * 60)
    print("[DEBUG] sign_up_web() — requête reçue")
    print(f"[DEBUG] body.nom_utilisateur : {body.nom_utilisateur}")
    print(f"[DEBUG] body.email           : {body.email}")
    print("=" * 60)

    try:
        user = insert_new_user(body)
        print(f"[DEBUG] insert_new_user() OK — user_id : {user.user_id}")

    except ValueError as e:
        print(f"[DEBUG] ❌ ValueError : {e}")
        return JSONResponse(
            status_code=409,
            content=SignUpWebResponse(
                success=False,
                message=str(e),
            ).model_dump(),
        )

    except Exception as e:
        print(f"[DEBUG] ❌ Exception inattendue : {type(e).__name__} — {e}")
        return JSONResponse(
            status_code=500,
            content=SignUpWebResponse(
                success=False,
                message="Une erreur interne est survenue. Veuillez réessayer.",
            ).model_dump(),
        )

    response = JSONResponse(
        status_code=200,
        content=SignUpWebResponse(
            success=True,
            message="Compte créé avec succès.",
            user_id=user.user_id,
        ).model_dump(),
    )

    # ── Pose des 3 cookies HttpOnly ──────────────────────
    response.set_cookie(key="session_user_id",     value=user.user_id,     **COOKIE_OPTS)
    response.set_cookie(key="session_identifiant", value=user.identifiant, **COOKIE_OPTS)
    response.set_cookie(key="session_email",       value=user.email,       **COOKIE_OPTS)

    print("[DEBUG] ✅ Cookies posés :")
    print(f"  session_user_id     : {user.user_id}")
    print(f"  session_identifiant : {user.identifiant}")
    print(f"  session_email       : {user.email}")
    print("[DEBUG] Réponse 201 envoyée")
    print("=" * 60)

    return response
