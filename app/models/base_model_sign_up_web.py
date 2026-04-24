# ================================================
# base_model_sign_up_web.py
# Modèle Pydantic — reçoit le JSON du front-end
# ================================================
#
# JSON attendu depuis sign_up.tsx :
# {
#   "nom":             "Dupont",
#   "prenom":          "Jean",
#   "email":           "jean.dupont@email.com",
#   "nom_utilisateur": "jean_dupont",
#   "mot_de_passe":    "monMotDePasse123",
#   "date_naissance":  "1990-05-14"
# }

from pydantic import BaseModel, EmailStr, field_validator


class SignUpWebRequest(BaseModel):
    nom:             str
    prenom:          str
    email:           EmailStr
    nom_utilisateur: str
    mot_de_passe:    str
    date_naissance:  str

    # ── Validations ──────────────────────────────

    @field_validator("nom", "prenom", "nom_utilisateur")
    @classmethod
    def not_empty(cls, v: str, info) -> str:
        if not v.strip():
            raise ValueError(f"{info.field_name} ne peut pas être vide.")
        return v.strip()

    @field_validator("nom_utilisateur")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Le nom d'utilisateur doit faire au moins 3 caractères.")
        return v

    @field_validator("mot_de_passe")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit faire au moins 8 caractères.")
        return v


class SignUpWebResponse(BaseModel):
    success: bool
    message: str
    user_id: str | None = None
