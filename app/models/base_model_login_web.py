# ================================================
# base_model_login_web.py
# Modèle Pydantic — reçoit le JSON du front-end
# ================================================
#
# JSON attendu depuis login_api_web.ts :
# {
#   "identifiant":  "jean_dupont",
#   "mot_de_passe": "monMotDePasse123"
# }

from pydantic import BaseModel


class LoginWebRequest(BaseModel):
    identifiant:  str
    mot_de_passe: str


class LoginWebResponse(BaseModel):
    success:  bool
    message:  str
    user_id:  str | None = None
