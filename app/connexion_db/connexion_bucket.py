import os
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

BUCKET_NAME = "collect_audio"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def upload_audio(file_bytes: bytes, file_name: str) -> str:
    """Upload un fichier audio dans le bucket. Retourne l'URL publique."""
    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_name,
        file=file_bytes,
        file_options={"content-type": "audio/mpeg"}
    )
    return get_public_url(file_name)


def delete_audio(file_name: str) -> None:
    """Supprime un fichier audio du bucket."""
    supabase.storage.from_(BUCKET_NAME).remove([file_name])


def list_audios() -> list:
    """Liste tous les fichiers dans le bucket."""
    return supabase.storage.from_(BUCKET_NAME).list()


def download_audio(file_name: str) -> bytes:
    """Télécharge un fichier audio depuis le bucket."""
    return supabase.storage.from_(BUCKET_NAME).download(file_name)


def get_public_url(file_name: str) -> str:
    """Retourne l'URL publique d'un fichier audio."""
    return supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)



def upload_image(file_bytes: bytes, file_name: str) -> str:
    """Upload une image dans le bucket. Retourne l'URL publique."""
    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_name,
        file=file_bytes,
        file_options={"content-type": "image/jpeg"}
    )
    return get_public_url(file_name)
