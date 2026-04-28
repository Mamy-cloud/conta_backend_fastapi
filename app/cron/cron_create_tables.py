# ================================================
# cron_create_tables.py
# Création des tables + colonnes en SQL pur
# Au démarrage et toutes les 3 minutes
# ================================================

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text
from app.connexion_db.connexion_db import engine

scheduler = AsyncIOScheduler()

# ── SQL pur ───────────────────────────────────────────────────────────────────

SQL_CREATE_AND_MIGRATE = """

-- ── login_user ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS login_user (
    id             TEXT PRIMARY KEY,
    identifiant    TEXT NOT NULL UNIQUE,
    password       TEXT NOT NULL,
    nom            TEXT,
    prenom         TEXT,
    email          TEXT UNIQUE,
    date_naissance TEXT,
    created_at     TEXT NOT NULL
);

ALTER TABLE login_user ADD COLUMN IF NOT EXISTS nom            TEXT;
ALTER TABLE login_user ADD COLUMN IF NOT EXISTS prenom         TEXT;
ALTER TABLE login_user ADD COLUMN IF NOT EXISTS email          TEXT UNIQUE;
ALTER TABLE login_user ADD COLUMN IF NOT EXISTS date_naissance TEXT;
ALTER TABLE login_user ADD COLUMN IF NOT EXISTS created_at     TEXT;

-- ── info_perso_temoin ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS info_perso_temoin (
    id             TEXT PRIMARY KEY,
    user_id        TEXT REFERENCES login_user(id),
    nom            TEXT NOT NULL,
    prenom         TEXT NOT NULL,
    date_naissance TEXT,
    departement    TEXT,
    region         TEXT,
    img_temoin     TEXT,
    contacts       TEXT NOT NULL DEFAULT '[]',
    signature_url  TEXT,
    accepte_rgpd   INTEGER NOT NULL DEFAULT 0 CHECK (accepte_rgpd IN (0, 1)),
    date_creation  TEXT NOT NULL
);

ALTER TABLE info_perso_temoin ADD COLUMN IF NOT EXISTS departement    TEXT;
ALTER TABLE info_perso_temoin ADD COLUMN IF NOT EXISTS region         TEXT;
ALTER TABLE info_perso_temoin ADD COLUMN IF NOT EXISTS img_temoin     TEXT;
ALTER TABLE info_perso_temoin ADD COLUMN IF NOT EXISTS signature_url  TEXT;
ALTER TABLE info_perso_temoin ADD COLUMN IF NOT EXISTS nom_departement TEXT;
ALTER TABLE info_perso_temoin ADD COLUMN IF NOT EXISTS nom_region      TEXT;

-- ── collect_info_from_temoin ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS collect_info_from_temoin (
    id                       TEXT PRIMARY KEY,
    user_id                  TEXT NOT NULL REFERENCES login_user(id),
    questionnaire            TEXT NOT NULL DEFAULT '[]',
    url_audio                TEXT,
    duree_audio              INTEGER NOT NULL DEFAULT 0,
    synced                   INTEGER NOT NULL DEFAULT 0 CHECK (synced IN (0, 1)),
    id_questionnaire         TEXT UNIQUE,
    traitement_transcription INTEGER NOT NULL DEFAULT 0 CHECK (traitement_transcription IN (0, 1)),
    created_at               TEXT NOT NULL
);

ALTER TABLE collect_info_from_temoin ADD COLUMN IF NOT EXISTS url_audio                TEXT;
ALTER TABLE collect_info_from_temoin ADD COLUMN IF NOT EXISTS id_questionnaire         TEXT UNIQUE;
ALTER TABLE collect_info_from_temoin ADD COLUMN IF NOT EXISTS traitement_transcription INTEGER NOT NULL DEFAULT 0;

-- ── info_perso_temoin_collect ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS info_perso_temoin_collect (
    id         TEXT PRIMARY KEY,
    collect_id TEXT NOT NULL REFERENCES collect_info_from_temoin(id),
    created_at TEXT NOT NULL
);

-- ── segmentation_audio ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS segmentation_audio (
    id         TEXT PRIMARY KEY,
    collect_id TEXT NOT NULL UNIQUE REFERENCES collect_info_from_temoin(id),
    validation INTEGER NOT NULL DEFAULT 0 CHECK (validation IN (0, 1)),
    created_at TEXT NOT NULL
);

ALTER TABLE segmentation_audio ADD COLUMN IF NOT EXISTS collect_id TEXT;
ALTER TABLE segmentation_audio ADD COLUMN IF NOT EXISTS validation INTEGER NOT NULL DEFAULT 0;
ALTER TABLE segmentation_audio ADD COLUMN IF NOT EXISTS created_at TEXT;

-- ── list_segmentation ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS list_segmentation (
    id                TEXT PRIMARY KEY,
    segmentation_id   TEXT NOT NULL REFERENCES segmentation_audio(id),
    debut             TEXT NOT NULL,
    fin               TEXT NOT NULL,
    segmentation_word TEXT NOT NULL DEFAULT '',
    created_at        TEXT NOT NULL
);

ALTER TABLE list_segmentation ADD COLUMN IF NOT EXISTS debut             TEXT;
ALTER TABLE list_segmentation ADD COLUMN IF NOT EXISTS fin               TEXT;
ALTER TABLE list_segmentation ADD COLUMN IF NOT EXISTS segmentation_word TEXT;
ALTER TABLE list_segmentation ADD COLUMN IF NOT EXISTS created_at        TEXT;

"""


def job_check_tables() -> None:
    """
    Exécute le SQL de création et migration.
    CREATE TABLE IF NOT EXISTS  → crée seulement si absente.
    ADD COLUMN IF NOT EXISTS    → ajoute seulement si absente.
    Aucune donnée existante n'est modifiée.
    """
    print("[CRON] Vérification des tables et colonnes...")
    try:
        with engine.connect() as conn:
            conn.execute(text(SQL_CREATE_AND_MIGRATE))
            conn.commit()
        print("[CRON] ✅ Tables et colonnes vérifiées.")
    except Exception as e:
        print(f"[CRON] ❌ Erreur : {type(e).__name__} — {e}")


def start_scheduler() -> None:
    scheduler.add_job(
        job_check_tables,
        trigger          = "interval",
        minutes          = 3,
        id               = "check_tables",
        replace_existing = True,
    )
    scheduler.start()
    print("[CRON] ✅ Scheduler démarré — vérification toutes les 3 minutes.")
