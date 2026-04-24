from pydantic import BaseModel, Field
from typing import Optional, List, Any


class QuestionnaireItem(BaseModel):
    champ:  str
    valeur: Any = None


class TemoinFromMobile(BaseModel):
    id:             Optional[str] = None
    user_id:        Optional[str] = None
    nom:            Optional[str] = None
    prenom:         Optional[str] = None
    date_naissance: Optional[str] = None
    departement:    Optional[str] = None
    region:         Optional[str] = None
    contacts:       Optional[str] = Field(default="[]")
    signature_url:  Optional[str] = None
    accepte_rgpd:   Optional[int] = 0
    date_creation:  Optional[str] = None


class CollecteFromMobile(BaseModel):
    user_id:          str
    temoin:           TemoinFromMobile
    questionnaire:    List[QuestionnaireItem] = []
    id_questionnaire: Optional[str] = None     # ← identifiant unique anti-doublon


# ─── Vérification des doublons ────────────────────────────────────────────────

class CheckIdsRequest(BaseModel):
    """Le mobile envoie tous ses id_questionnaire non synchronisés."""
    user_id:           str
    id_questionnaires: List[str]


class CheckIdsResponse(BaseModel):
    """FastAPI retourne uniquement les ids qui n'existent PAS encore en DB."""
    ids_a_transferer: List[str]   # ids absents → à transférer
    ids_deja_synced:  List[str]   # ids déjà présents → à ignorer
    total_envoye:     int
    total_a_transferer: int


# ─── Sync response ────────────────────────────────────────────────────────────

class SyncResponse(BaseModel):
    success:          bool
    collect_id:       Optional[str] = None
    id_questionnaire: Optional[str] = None
    audio_url:        Optional[str] = None
    image_url:        Optional[str] = None
    message:          Optional[str] = None


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    identifiant: str
    password:    str


class LoginResponse(BaseModel):
    success:    bool
    user_id:    Optional[str] = None
    token:      Optional[str] = None
    message:    Optional[str] = None
