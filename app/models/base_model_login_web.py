# ================================================
# base_model_login_web.py
# ================================================

from typing import Optional
from pydantic import BaseModel


class LoginWebRequest(BaseModel):
    identifiant:  str
    mot_de_passe: str


class LoginWebResponse(BaseModel):
    success:  bool
    message:  str
    user_id:  Optional[str] = None
