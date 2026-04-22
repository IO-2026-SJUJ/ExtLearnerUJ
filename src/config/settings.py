"""
Django settings for ExtLearnerUJ project.

Wrażliwe dane czytamy z pliku .env (patrz .env.example).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ('1', 'true', 'yes', 'on')


# ============================================================
# Core
# ============================================================
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'dev-only-secret-do-not-use-in-prod-xxxxxxxxxxxxxxxxxxxx'
)
DEBUG = _bool('DJANGO_DEBUG', True)
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
]

# ============================================================
# Applications
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ExtLearnerUJ',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Nasz własny middleware — ustawia request.app_user na podstawie
    # ciasteczka 'session_token' (patrz ExtLearnerUJ/middleware.py).
    'ExtLearnerUJ.middleware.SessionAuthMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Własny context processor — udostępnia `app_user` we wszystkich
                # szablonach, żeby base.html mogło pokazywać stan zalogowania.
                'ExtLearnerUJ.context_processors.app_user',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ============================================================
# Database (Sprint 1 — SQLite; Sprint 2+ — Postgres/Supabase EU)
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'TEST': {
            'NAME': BASE_DIR / 'test_db.sqlite3',
        },
    }
}

# ============================================================
# Hasła — Argon2 jako domyślny hasher (NFR-03)
# ============================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# Email
# ============================================================
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'noreply@extlearner.uj.edu.pl')

# ============================================================
# Lokalizacja / czas
# ============================================================
LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

# ============================================================
# Static / Media
# ============================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []  # aplikacja ExtLearnerUJ ma własny static/ (APP_DIRS)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# Sesje aplikacyjne (nasze własne, NIE Django session framework)
# ============================================================
SESSION_COOKIE_NAME_APP = 'session_token'
SESSION_LIFETIME_HOURS = 24
SESSION_REFRESH_THRESHOLD_HOURS = 1  # auto-refresh gdy <1h do wygaśnięcia

SECURE_COOKIES = _bool('SECURE_COOKIES', False)  # w produkcji True (tylko HTTPS)

# ============================================================
# Różne
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Limit rozmiaru uploadu plików materiałów (Sprint 2, ale ustawiamy od razu)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
