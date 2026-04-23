import json
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.connexion_db.connexion_bucket import upload_audio, upload_image
from app.models.base_model_from_mobile import (
    CollecteFromMobile,
    TemoinFromMobile,
    QuestionnaireItem,
    SyncResponse,
)
from app.request_command.request_create_table import (
    LoginUser,
    InfoPersoTemoin,
    CollectInfoFromTemoin,
    InfoPersoTemoinCollect,
)
import logging
logger = logging.getLogger(__name__)



# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.utcnow().isoformat()


def _safe_uuid(value: str | None) -> str:
    return value if value else str(uuid.uuid4())


# ─── Upsert témoin ────────────────────────────────────────────────────────────

def _upsert_temoin(
    db: Session,
    temoin_data: TemoinFromMobile,
    image_url: str | None,
) -> InfoPersoTemoin:
    """
    Crée ou met à jour le témoin dans info_perso_temoin.
    Retourne l'objet SQLAlchemy.
    """
    temoin_id = _safe_uuid(temoin_data.id)

    temoin = db.query(InfoPersoTemoin).filter(
        InfoPersoTemoin.id == temoin_id
    ).first()

    if temoin is None:
        temoin = InfoPersoTemoin(
            id             = temoin_id,
            user_id        = temoin_data.user_id,
            nom            = temoin_data.nom            or "",
            prenom         = temoin_data.prenom         or "",
            date_naissance = temoin_data.date_naissance,
            departement    = temoin_data.departement,
            region         = temoin_data.region,
            img_temoin     = image_url or temoin_data.img_temoin,
            contacts       = temoin_data.contacts       or "[]",
            signature_url  = temoin_data.signature_url,
            accepte_rgpd   = temoin_data.accepte_rgpd   or 0,
            date_creation  = temoin_data.date_creation  or _now(),
        )
        db.add(temoin)
    else:
        # Met à jour uniquement les champs non nuls
        if temoin_data.nom:            temoin.nom            = temoin_data.nom
        if temoin_data.prenom:         temoin.prenom         = temoin_data.prenom
        if temoin_data.date_naissance: temoin.date_naissance = temoin_data.date_naissance
        if temoin_data.departement:    temoin.departement    = temoin_data.departement
        if temoin_data.region:         temoin.region         = temoin_data.region
        if temoin_data.contacts:       temoin.contacts       = temoin_data.contacts
        if temoin_data.signature_url:  temoin.signature_url  = temoin_data.signature_url
        if temoin_data.accepte_rgpd:   temoin.accepte_rgpd   = temoin_data.accepte_rgpd
        if image_url:                  temoin.img_temoin     = image_url

    db.flush()
    return temoin


# ─── Upsert collecte ──────────────────────────────────────────────────────────

def _upsert_collecte(
    db: Session,
    user_id: str,
    questionnaire: list[QuestionnaireItem],
    audio_url: str | None,
    duree_audio: int,
) -> CollectInfoFromTemoin:
    """
    Crée une nouvelle collecte dans collect_info_from_temoin.
    Retourne l'objet SQLAlchemy.
    """
    collecte_id = str(uuid.uuid4())

    collecte = CollectInfoFromTemoin(
        id            = collecte_id,
        user_id       = user_id,
        questionnaire = json.dumps(
            [item.model_dump() for item in questionnaire],
            ensure_ascii=False,
        ),
        url_audio     = audio_url,
        duree_audio   = duree_audio,
        synced        = 1,          # déjà synchronisé côté serveur
        created_at    = _now(),
    )
    db.add(collecte)
    db.flush()
    return collecte


# ─── Lien info_perso_temoin_collect ──────────────────────────────────────────

def _create_link(db: Session, collecte_id: str) -> None:
    """Crée l'entrée de liaison dans info_perso_temoin_collect."""
    link = InfoPersoTemoinCollect(
        id         = str(uuid.uuid4()),
        collect_id = collecte_id,
        created_at = _now(),
    )
    db.add(link)
    db.flush()


# ─── Fonction principale ──────────────────────────────────────────────────────

async def handle_sync_from_mobile(
    db: Session,
    user_id: str,
    temoin_json: str,
    questionnaire_json: str,
    audio_file: UploadFile | None = None,
    image_file: UploadFile | None = None,
    duree_audio: int = 0,
) -> SyncResponse:
    """
    Point d'entrée appelé par l'endpoint POST /sync.

    Étapes :
      1. Parse les JSON temoin + questionnaire
      2. Upload audio  → bucket Supabase collect_audio
      3. Upload image  → bucket Supabase collect_audio
      4. Upsert témoin → table info_perso_temoin
      5. Crée collecte → table collect_info_from_temoin  (synced = 1)
      6. Crée lien     → table info_perso_temoin_collect
      7. Commit
    """
    try:
        # 1. Parse JSON ────────────────────────────────────────────────────────
        temoin_data = TemoinFromMobile.model_validate_json(temoin_json)

        questionnaire_raw = json.loads(questionnaire_json)
        questionnaire = [QuestionnaireItem(**item) for item in questionnaire_raw]

        # 2. Upload audio ──────────────────────────────────────────────────────
        audio_url: str | None = None
        if audio_file and audio_file.filename:
            audio_bytes    = await audio_file.read()
            audio_filename = f"audio/{user_id}/{uuid.uuid4()}_{audio_file.filename}"
            audio_url      = upload_audio(audio_bytes, audio_filename)

        # 3. Upload image ──────────────────────────────────────────────────────
        image_url: str | None = None
        if image_file and image_file.filename:
            image_bytes    = await image_file.read()
            image_filename = f"image/{user_id}/{uuid.uuid4()}_{image_file.filename}"
            image_url      = upload_image(image_bytes, image_filename)

        # 4. Upsert témoin ─────────────────────────────────────────────────────
        temoin = _upsert_temoin(db, temoin_data, image_url)

        # 5. Crée collecte ─────────────────────────────────────────────────────
        collecte = _upsert_collecte(
            db            = db,
            user_id       = user_id,
            questionnaire = questionnaire,
            audio_url     = audio_url,
            duree_audio   = duree_audio,
        )

        # 6. Crée lien ─────────────────────────────────────────────────────────
        _create_link(db, collecte.id)

        # 7. Commit ────────────────────────────────────────────────────────────
        db.commit()

        return SyncResponse(
            success    = True,
            collect_id = collecte.id,
            audio_url  = audio_url,
            image_url  = image_url,
            message    = "Synchronisation réussie",
        )

    except Exception as e:
        db.rollback()
        return SyncResponse(
            success = False,
            message = f"Erreur synchronisation : {str(e)}",
        )
