# ================================================
# sign_up_web.py
# Endpoint POST /sign_up/web
# ================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.base_model_sign_up_web  import SignUpWebRequest, SignUpWebResponse
from app.request_command.sign_up.update_table_sign_up_web import insert_new_user

router = APIRouter()


@router.post(
    "/sign_up/web",
    response_model=SignUpWebResponse,
    summary="Inscription d'un nouvel utilisateur web",
    tags=["Auth"],
)
async def sign_up_web(body: SignUpWebRequest) -> JSONResponse:
    """
    Reçoit le formulaire d'inscription du front-end React,
    valide les données et insère l'utilisateur dans login_user.

    Corps JSON attendu :
    ```json
    {
      "nom":             "Dupont",
      "prenom":          "Jean",
      "email":           "jean.dupont@email.com",
      "nom_utilisateur": "jean_dupont",
      "mot_de_passe":    "monMotDePasse123",
      "date_naissance":  "1990-05-14"
    }
    ```
    """

    try:
        user_id = insert_new_user(body)

    except ValueError as e:
        return JSONResponse(
            status_code=409,
            content=SignUpWebResponse(
                success=False,
                message=str(e),
            ).model_dump(),
        )

    except Exception:
        return JSONResponse(
            status_code=500,
            content=SignUpWebResponse(
                success=False,
                message="Une erreur interne est survenue. Veuillez réessayer.",
            ).model_dump(),
        )

    return JSONResponse(
        status_code=201,
        content=SignUpWebResponse(
            success=True,
            message="Compte créé avec succès.",
            user_id=user_id,
        ).model_dump(),
    )
