# ================================================
# save_segmentation.py
# Sauvegarde les segments STT en DB
# et gère la validation des transcriptions
# ================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.connexion_db.connexion_db import engine
from app.request_command.request_create_table import (
    SegmentationAudio,
    ListSegmentation,
    CollectInfoFromTemoin,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Sauvegarde des segments ───────────────────────────────────────────────────

def save_segments(collect_id: str, segments: list[dict]) -> str:
    """
    Crée ou met à jour un enregistrement segmentation_audio
    et insère les segments dans list_segmentation.

    segments : [{ "debut": "00:00", "fin": "00:13", "texte": "..." }, ...]
    Retourne le segmentation_id.
    """

    with Session(engine) as session:

        # ── Vérifie si une segmentation existe déjà ──
        stmt = select(SegmentationAudio).where(
            SegmentationAudio.collect_id == collect_id
        )
        existing = session.scalars(stmt).first()

        if existing:
            # Supprime les anciens segments
            session.query(ListSegmentation).filter(
                ListSegmentation.segmentation_id == existing.id
            ).delete()
            seg_audio = existing
            seg_id    = existing.id
        else:
            seg_id    = str(uuid.uuid4())
            seg_audio = SegmentationAudio(
                id         = seg_id,
                collect_id = collect_id,
                validation = 0,
                created_at = _now(),
            )
            session.add(seg_audio)

        # ── Insère les nouveaux segments ──────────────
        for s in segments:
            session.add(ListSegmentation(
                id                = str(uuid.uuid4()),
                segmentation_id   = seg_id,
                debut             = s.get("debut", "00:00"),
                fin               = s.get("fin",   "00:00"),
                segmentation_word = s.get("texte", ""),
                created_at        = _now(),
            ))

        session.commit()

    return seg_id


# ── Chargement des segments existants ────────────────────────────────────────

def load_segments(collect_id: str) -> dict | None:
    """
    Retourne les segments existants si la segmentation existe.
    { "segmentation_id": str, "validation": bool, "segments": [...] }
    ou None si pas de segmentation.
    """

    with Session(engine) as session:
        stmt = select(SegmentationAudio).where(
            SegmentationAudio.collect_id == collect_id
        )
        seg_audio = session.scalars(stmt).first()

        if not seg_audio:
            return None

        segments = session.query(ListSegmentation).filter(
            ListSegmentation.segmentation_id == seg_audio.id
        ).order_by(ListSegmentation.debut).all()

        return {
            "segmentation_id": seg_audio.id,
            "validation":      bool(seg_audio.validation),
            "segments": [
                {
                    "id":                s.id,
                    "debut":             s.debut,
                    "fin":               s.fin,
                    "segmentation_word": s.segmentation_word,
                }
                for s in segments
            ],
        }


# ── Validation — 3 transcripteurs ont validé ─────────────────────────────────

def validate_segmentation(collect_id: str) -> None:
    """
    Passe validation = 1 dans segmentation_audio
    ET traitement_transcription = 1 dans collect_info_from_temoin.
    Appelé quand les 3 transcripteurs ont validé.
    """

    with Session(engine) as session:

        # ── segmentation_audio → validation = 1 ──────
        stmt = select(SegmentationAudio).where(
            SegmentationAudio.collect_id == collect_id
        )
        seg_audio = session.scalars(stmt).first()
        if seg_audio:
            seg_audio.validation = 1

        # ── collect_info_from_temoin → traitement_transcription = 1 ──
        collect = session.get(CollectInfoFromTemoin, collect_id)
        if collect:
            collect.traitement_transcription = 1

        session.commit()
        print(f"[SEGMENTATION] ✅ Validé pour collect_id={collect_id}")


# ── Mise à jour d'un segment (texte corrigé) ─────────────────────────────────

def update_segment_word(segment_id: str, new_text: str) -> None:
    """Met à jour le texte d'un segment."""
    with Session(engine) as session:
        seg = session.get(ListSegmentation, segment_id)
        if seg:
            seg.segmentation_word = new_text
            session.commit()
