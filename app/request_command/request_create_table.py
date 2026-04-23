from connexion_db.connexion_db import engine, Base
from sqlalchemy import (
    Column, Text, Integer, ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import relationship


# ─── Modèles ──────────────────────────────────────────────────────────────────

class LoginUser(Base):
    __tablename__ = "login_user"

    id             = Column(Text, primary_key=True)
    identifiant    = Column(Text, nullable=False, unique=True)
    password       = Column(Text, nullable=False)
    email          = Column(Text, nullable=True, unique=True)
    date_naissance = Column(Text, nullable=True)
    created_at     = Column(Text, nullable=False)

    # Relations
    infos_perso = relationship("InfoPersoTemoin",       back_populates="user")
    collectes   = relationship("CollectInfoFromTemoin", back_populates="user")


class InfoPersoTemoin(Base):
    __tablename__ = "info_perso_temoin"

    id             = Column(Text, primary_key=True)
    user_id        = Column(Text, ForeignKey("login_user.id"), nullable=True)
    nom            = Column(Text, nullable=False)
    prenom         = Column(Text, nullable=False)
    date_naissance = Column(Text, nullable=True)
    departement    = Column(Text, nullable=True)
    region         = Column(Text, nullable=True)
    img_temoin     = Column(Text, nullable=True)
    contacts       = Column(Text, nullable=False, default="[]")
    signature_url  = Column(Text, nullable=True)
    accepte_rgpd   = Column(Integer, nullable=False, default=0)
    date_creation  = Column(Text, nullable=False)

    # Relations
    user = relationship("LoginUser", back_populates="infos_perso")

    __table_args__ = (
        CheckConstraint("accepte_rgpd IN (0, 1)", name="chk_accepte_rgpd"),
    )


class CollectInfoFromTemoin(Base):
    __tablename__ = "collect_info_from_temoin"

    id            = Column(Text, primary_key=True)
    user_id       = Column(Text, ForeignKey("login_user.id"), nullable=False)
    questionnaire = Column(Text, nullable=False, default="[]")
    url_audio     = Column(Text, nullable=True)
    duree_audio   = Column(Integer, nullable=False, default=0)
    synced        = Column(Integer, nullable=False, default=0)
    created_at    = Column(Text, nullable=False)

    # Relations
    user              = relationship("LoginUser",               back_populates="collectes")
    info_perso_linked = relationship("InfoPersoTemoinCollect",  back_populates="collecte")

    __table_args__ = (
        CheckConstraint("synced IN (0, 1)", name="chk_synced"),
    )


class InfoPersoTemoinCollect(Base):
    __tablename__ = "info_perso_temoin_collect"

    id         = Column(Text, primary_key=True)
    collect_id = Column(Text, ForeignKey("collect_info_from_temoin.id"), nullable=False)
    created_at = Column(Text, nullable=False)

    # Relations
    collecte = relationship("CollectInfoFromTemoin", back_populates="info_perso_linked")


# ─── Création / suppression des tables ────────────────────────────────────────

def create_all_tables() -> None:
    """Crée toutes les tables si elles n'existent pas."""
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès.")
    print("   → login_user")
    print("   → info_perso_temoin")
    print("   → collect_info_from_temoin")
    print("   → info_perso_temoin_collect")


def drop_all_tables() -> None:
    """Supprime toutes les tables — dev uniquement ⚠️"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  Toutes les tables ont été supprimées.")


if __name__ == "__main__":
    create_all_tables()
