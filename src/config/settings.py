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

# Wymagane przez Django dla żądań POST przez HTTPS spoza localhost
# (np. formularze na produkcyjnej domenie). Ustawiane zmienną środowiskową,
# np. "https://olejnik.net,https://www.olejnik.net".
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
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

# WhiteNoise serwuje pliki statyczne w produkcji (przy DEBUG=False), bez
# osobnego serwera WWW. Włączamy tylko, gdy pakiet jest dostępny — dzięki temu
# środowiska bez whitenoise (np. lokalne testy) działają bez zmian.
try:
    import whitenoise  # noqa: F401
    _HAS_WHITENOISE = True
except ImportError:
    _HAS_WHITENOISE = False

if _HAS_WHITENOISE:
    # Tuż po SecurityMiddleware (zalecane przez WhiteNoise).
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

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
                'django.template.context_processors.media',
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
# Database — czytane z DATABASE_URL.
#   * brak zmiennej lub "sqlite:///..." -> lokalny SQLite (dev/testy),
#   * "postgres://..." / "postgresql://..." -> PostgreSQL (produkcja, np.
#     zarządzana baza na Render w regionie EU — wymóg RODO O-01).
# Parser oparty o bibliotekę standardową, więc import settings nie wymaga
# dodatkowych pakietów; sterownik psycopg jest potrzebny dopiero przy
# realnym połączeniu z Postgresem (patrz requirements.txt).
# ============================================================
import urllib.parse as _urlparse


def _database_from_url(url: str):
    if not url or url.startswith('sqlite'):
        name = BASE_DIR / 'db.sqlite3'
        if url.startswith('sqlite:///') and url[len('sqlite:///'):]:
            name = url[len('sqlite:///'):]
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': name,
            'TEST': {'NAME': BASE_DIR / 'test_db.sqlite3'},
        }
    parsed = _urlparse.urlparse(url)
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path.lstrip('/'),
        'USER': _urlparse.unquote(parsed.username or ''),
        'PASSWORD': _urlparse.unquote(parsed.password or ''),
        'HOST': parsed.hostname or '',
        'PORT': str(parsed.port or ''),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {'sslmode': 'require'},  # szyfrowanie połączenia (RODO)
    }


DATABASES = {'default': _database_from_url(os.getenv('DATABASE_URL', ''))}

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
# ============================================================
# Email
# ============================================================
# Realne wysyłanie maili (kody weryfikacyjne, reset hasła): gdy ustawisz
# EMAIL_HOST w .env, używamy SMTP. Bez tego — backend konsolowy (treść
# maila ląduje w konsoli serwera, wygodne w dev). Backend można też wymusić
# wprost przez EMAIL_BACKEND.
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = _bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = _bool('EMAIL_USE_SSL', False)

# Resend — wysyłka maili przez HTTPS (działa tam, gdzie SMTP jest zablokowany,
# np. darmowy plan Render). Gdy ustawisz RESEND_API_KEY, ma pierwszeństwo.
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')

if os.getenv('EMAIL_BACKEND'):
    EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
elif RESEND_API_KEY:
    EMAIL_BACKEND = 'ExtLearnerUJ.email_backends.ResendEmailBackend'
elif EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    # Dev bez SMTP — drukujemy maile do konsoli (widać kod weryfikacyjny).
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    EMAIL_HOST_USER or 'noreply@extlearner.uj.edu.pl',
)

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

if _HAS_WHITENOISE:
    # Skompresowane pliki statyczne z hashem w nazwie (cache-busting).
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

# ============================================================
# Sesje aplikacyjne (nasze własne, NIE Django session framework)
# ============================================================
SESSION_COOKIE_NAME_APP = 'session_token'
SESSION_LIFETIME_HOURS = 24
SESSION_REFRESH_THRESHOLD_HOURS = 1  # auto-refresh gdy <1h do wygaśnięcia

SECURE_COOKIES = _bool('SECURE_COOKIES', False)  # w produkcji True (tylko HTTPS)

# Render (i inne PaaS) kończą TLS na proxy i przekazują oryginalny schemat
# w nagłówku X-Forwarded-Proto — dzięki temu Django wie, że żądanie jest po HTTPS.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES
SECURE_SSL_REDIRECT = SECURE_COOKIES  # wymuś HTTPS w produkcji

# ============================================================
# Różne
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Limit rozmiaru uploadu plików materiałów (Sprint 2, ale ustawiamy od razu)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
