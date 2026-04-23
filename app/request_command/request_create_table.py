import logging
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.connexion_cloud.connexion_db import Base, engine

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# LOGIN USER
# ─────────────────────────────────────────────

class LoginUser(Base):
    __tablename__ = "login_user"

    id = Column(String, primary_key=True)
    identifiant = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)

    email = Column(String(255), nullable=True, unique=True)
    date_naissance = Column(String, nullable=True)
    created_at = Column(String, nullable=False)

    infos_perso = relationship(
        "InfoPersoTemoin",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    collectes = relationship(
        "CollectInfoFromTemoin",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# ─────────────────────────────────────────────
# INFO TEMOIN
# ─────────────────────────────────────────────

class InfoPersoTemoin(Base):
    __tablename__ = "info_perso_temoin"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("login_user.id"), nullable=True)

    nom = Column(String(255), nullable=False)
    prenom = Column(String(255), nullable=False)

    date_naissance = Column(String, nullable=True)
    departement = Column(String, nullable=True)
    region = Column(String, nullable=True)

    img_temoin = Column(String, nullable=True)

    # JSON stocké proprement (string mais contrôlé)
    contacts = Column(String, nullable=False, default="[]")

    signature_url = Column(String, nullable=True)

    accepte_rgpd = Column(Integer, nullable=False, default=0)

    date_creation = Column(String, nullable=False)

    user = relationship("LoginUser", back_populates="infos_perso")

    __table_args__ = (
        CheckConstraint("accepte_rgpd IN (0, 1)", name="chk_accepte_rgpd"),
    )


# ─────────────────────────────────────────────
# COLLECT INFO
# ─────────────────────────────────────────────

class CollectInfoFromTemoin(Base):
    __tablename__ = "collect_info_from_temoin"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("login_user.id"), nullable=False)

    questionnaire = Column(String, nullable=False, default="[]")

    url_audio = Column(String, nullable=True)

    duree_audio = Column(Integer, nullable=False, default=0)

    synced = Column(Integer, nullable=False, default=0)

    created_at = Column(String, nullable=False)

    user = relationship("LoginUser", back_populates="collectes")

    info_perso_linked = relationship(
        "InfoPersoTemoinCollect",
        back_populates="collecte",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("synced IN (0, 1)", name="chk_synced"),
    )


# ─────────────────────────────────────────────
# LINK TABLE
# ─────────────────────────────────────────────

class InfoPersoTemoinCollect(Base):
    __tablename__ = "info_perso_temoin_collect"

    id = Column(String, primary_key=True)
    collect_id = Column(
        String,
        ForeignKey("collect_info_from_temoin.id"),
        nullable=False,
    )

    created_at = Column(String, nullable=False)

    collecte = relationship(
        "CollectInfoFromTemoin",
        back_populates="info_perso_linked",
    )


# ─────────────────────────────────────────────
# TABLE MANAGEMENT (SAFE PROD)
# ─────────────────────────────────────────────

def create_all_tables():
    """Création safe (DEV ONLY)."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès")
    except Exception as e:
        logger.error(f"Erreur création tables: {e}")
        raise


def drop_all_tables():
    """⚠️ DEV ONLY"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("Toutes les tables ont été supprimées")
    except Exception as e:
        logger.error(f"Erreur suppression tables: {e}")
        raise


if __name__ == "__main__":
    create_all_tables()