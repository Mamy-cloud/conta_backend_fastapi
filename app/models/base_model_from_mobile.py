from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ─── Questionnaire ────────────────────────────────────────────────────────────

class QuestionnaireItem(BaseModel):
    """Un champ du questionnaire ex: {'champ': 'temoin_id', 'valeur': 'xxx'}"""
    champ:  str
    valeur: Any = None


# ─── Témoin (info_perso_temoin) ───────────────────────────────────────────────

class TemoinFromMobile(BaseModel):
    """Données du témoin envoyées depuis le mobile (champ 'temoin' du multipart)."""
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


# ─── Collecte (collect_info_from_temoin) ─────────────────────────────────────

class CollecteFromMobile(BaseModel):
    """
    Payload complet reçu depuis le mobile via multipart/form-data sur POST /sync.

    Champs texte du multipart :
      - user_id       : identifiant de l'utilisateur
      - temoin        : JSON stringifié → TemoinFromMobile
      - questionnaire : JSON stringifié → List[QuestionnaireItem]

    Fichiers du multipart (optionnels) :
      - audio : fichier audio (géré via UploadFile dans l'endpoint)
      - image : photo du témoin (géré via UploadFile dans l'endpoint)
    """
    user_id:       str
    temoin:        TemoinFromMobile
    questionnaire: List[QuestionnaireItem] = []


# ─── Réponse FastAPI → Mobile ─────────────────────────────────────────────────

class SyncResponse(BaseModel):
    """Réponse renvoyée au mobile après un sync réussi."""
    success:    bool
    collect_id: Optional[str] = None
    audio_url:  Optional[str] = None
    image_url:  Optional[str] = None
    message:    Optional[str] = None


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Payload de connexion envoyé par le mobile."""
    identifiant: str
    password:    str


class LoginResponse(BaseModel):
    """Réponse après connexion réussie."""
    success:    bool
    user_id:    Optional[str] = None
    token:      Optional[str] = None
    message:    Optional[str] = None
