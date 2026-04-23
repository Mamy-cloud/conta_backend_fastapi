from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime


# ─────────────────────────────────────────────
# QUESTIONNAIRE ITEM
# ─────────────────────────────────────────────

class QuestionnaireItem(BaseModel):
    """Champ du questionnaire envoyé depuis le mobile."""
    champ: str
    valeur: Optional[Union[str, int, float, bool]] = None


# ─────────────────────────────────────────────
# TEMOIN
# ─────────────────────────────────────────────

class TemoinFromMobile(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None

    date_naissance: Optional[datetime] = None

    departement: Optional[str] = None
    region: Optional[str] = None

    # 🔥 FIX : vraie liste JSON (pas string)
    contacts: List[str] = Field(default_factory=list)

    signature_url: Optional[str] = None
    accepte_rgpd: int = 0

    date_creation: Optional[datetime] = None


# ─────────────────────────────────────────────
# COLLECTE MOBILE
# ─────────────────────────────────────────────

class CollecteFromMobile(BaseModel):
    user_id: str
    temoin: TemoinFromMobile
    questionnaire: List[QuestionnaireItem] = Field(default_factory=list)


# ─────────────────────────────────────────────
# SYNC RESPONSE
# ─────────────────────────────────────────────

class SyncResponse(BaseModel):
    success: bool
    collect_id: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    message: Optional[str] = None


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    identifiant: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None