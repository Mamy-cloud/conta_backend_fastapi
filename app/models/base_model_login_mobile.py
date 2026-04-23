# base_model_login_mobile.py
import logging
from pydantic import BaseModel, field_validator
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Requête envoyée par le mobile ────────────────────────────────────────────

class LoginMobileRequest(BaseModel):
    """JSON reçu depuis le mobile — plus d'id, FastAPI le récupère dans Supabase."""
    identifiant: str
    password:    str

    @field_validator("identifiant", "password")
    @classmethod
    def not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            logger.error(f"❌ Champ '{info.field_name}' vide dans LoginMobileRequest")
            raise ValueError(f"Le champ '{info.field_name}' ne peut pas être vide")
        logger.debug(f"Validation OK → champ='{info.field_name}'")
        return v.strip()


# ─── Réponses envoyées vers le mobile ─────────────────────────────────────────

class ServerStatusResponse(BaseModel):
    """Réponse initiale : confirme que le serveur est allumé."""
    success: bool
    message: str


class LoginMobileResponse(BaseModel):
    """Réponse après vérification — retourne l'id pour SQLite local."""
    success:        bool
    identifiant_ok: bool
    password_ok:    bool
    user_id:        Optional[str]  # id Supabase à stocker dans SQLite local
    message:        str
