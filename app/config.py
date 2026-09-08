"""Configuración central de la app: región, IDs de modelo y clave de cifrado.

Todo se lee de variables de entorno (ver .env.example). No se guardan
credenciales de AWS aquí: boto3/botocore resuelve la autenticación solo,
por dos vías posibles (ver README):
  1. Bedrock API key (bearer token): variable de entorno estándar
     AWS_BEARER_TOKEN_BEDROCK. `load_dotenv()` la copia de .env al entorno
     del proceso y boto3 la detecta automáticamente al crear el cliente de
     bedrock-runtime, sin necesidad de perfil.
  2. Perfil de AWS CLI/SSO (AWS_PROFILE) o credenciales de entorno/rol de
     instancia, para autenticación IAM estándar.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
LOGS_DIR = APP_DIR.parent / "logs"
DATA_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE") or None
USING_BEARER_TOKEN = bool(os.getenv("AWS_BEARER_TOKEN_BEDROCK"))

# Si AWS_PROFILE quedó vacío en .env, dotenv igual lo deja como "" en el entorno
# del proceso, y boto3 lo lee directamente (no a través de esta variable) e
# intenta cargar un perfil llamado "": lo retiramos del entorno para evitarlo.
if not AWS_PROFILE and os.environ.get("AWS_PROFILE") == "":
    del os.environ["AWS_PROFILE"]

# Modelo de imagen (Stability AI "Stable Image" en Bedrock). No todas las
# regiones tienen modelos de texto-a-imagen puro habilitados; permite una
# región distinta a AWS_REGION para este servicio (ver README).
IMAGE_MODEL_ID = os.getenv("BEDROCK_IMAGE_MODEL_ID", "stability.stable-image-core-v1:1")
IMAGE_REGION = os.getenv("BEDROCK_IMAGE_REGION") or AWS_REGION

# Modelo de texto (Claude en Bedrock). Los modelos recientes solo se invocan
# vía "inference profile" (prefijo de región, p. ej. "us." o "global."), no
# con el ID base del modelo.
TEXT_MODEL_ID = os.getenv("BEDROCK_TEXT_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")

# Modelo de embeddings (Titan) para RAG opcional sobre la guía de marca.
EMBED_MODEL_ID = os.getenv("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")

# Clave de cifrado simétrico (Fernet) para el almacenamiento local.
# Generar una propia con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
APP_ENCRYPTION_KEY = os.getenv("APP_ENCRYPTION_KEY", "")

# Modo demo: si es "true", no se llama a Bedrock de verdad y se usan
# respuestas simuladas. Útil si aún no tienes acceso a los modelos.
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

ROLES = ["Diseñador", "Redactor", "Aprobador"]

DEMO_USERS = {
    "Jorge Ivan": "Diseñador",
    "Camilo": "Redactor",
    "Pamela": "Aprobador",
}
