# ================================================
# endpoint_login_web.py
# Endpoint POST /login/web
# ================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.base_model_login_web import LoginWebRequest, LoginWebResponse
from app.request_command.login.verif_login_web import verify_login

router = APIRouter()


@router.post(
    "/login/web",
    response_model=LoginWebResponse,
    summary="Connexion d'un utilisateur web",
    tags=["Auth"],
)
async def login_web(body: LoginWebRequest) -> JSONResponse:
    """
    Reçoit les credentials du front-end React,
    vérifie l'identifiant et le mot de passe dans login_user.

    Corps JSON attendu :
    ```json
    {
      "identifiant":  "jean_dupont",
      "mot_de_passe": "monMotDePasse123"
    }
    ```

    Réponses :
    - 200 : connexion réussie → redirection vers /travail côté front
    - 401 : identifiant ou mot de passe incorrect
    - 500 : erreur interne
    """

    try:
        user_id = verify_login(body)

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

    return JSONResponse(
        status_code=200,
        content=LoginWebResponse(
            success=True,
            message="Connexion réussie.",
            user_id=user_id,
        ).model_dump(),
    )
