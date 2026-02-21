from pathlib import Path
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== Core ====================
SECRET_KEY = config("SECRET_KEY", default="changeme-para-dev")
DEBUG = config("DEBUG", cast=bool, default=False)

ALLOWED_HOSTS = [
    "tecnologiafya.site",
    "www.tecnologiafya.site",
    # agrega tu subdominio de PythonAnywhere si lo usas directamente:
    # "tuusuario.pythonanywhere.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tecnologiafya.site",
    "https://www.tecnologiafya.site",
    # si accedés por el dominio de PA con HTTPS:
    # "https://tuusuario.pythonanywhere.com",
]

# ==================== Apps ====================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "core",
    "productos",
    "accounts",
    "facturacion",
    "divisas",
    "axes",  # 🔒 Protección fuerza bruta
]

# ==================== Middleware ====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "accounts.middleware.AutoLogoutMiddleware",
    "accounts.middleware.RestrictIPMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "axes.backends.AxesBackend",
]

ROOT_URLCONF = "Importaciones_fya.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Importaciones_fya.wsgi.application"

# ==================== DB (PythonAnywhere MySQL) ====================
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.mysql"),
        "NAME": config("DB_NAME", default="importacionfya1$default"),
        "USER": config("DB_USER", default="importacionfya1"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config(
            "DB_HOST",
            default="importacionfya1.mysql.pythonanywhere-services.com",
        ),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ==================== Auth ====================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.Usuario"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ==================== I18N ====================
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# ==================== Static & Media ====================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # <- necesario en producción (collectstatic)
# Si además tenés assets de desarrollo:
# STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==================== Email ====================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ==================== Seguridad (producción) ====================
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 0  # en PA podés forzar HTTPS desde el panel; dejalo en 0 si no configuraste HSTS
SECURE_SSL_REDIRECT = False  # en PA normalmente se fuerza HTTPS desde el panel

# ==================== Axes (detrás de proxy) ====================
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 5  # horas
AXES_LOCKOUT_TEMPLATE = "accounts/lockout.html"
AXES_RESET_ON_SUCCESS = True
AXES_BEHIND_REVERSE_PROXY = True
AXES_META_PRECEDENCE_ORDER = (
    "HTTP_X_FORWARDED_FOR",
    "REMOTE_ADDR",
)

# ==================== Mensajes ====================
from django.contrib.messages import constants as messages
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
MESSAGE_TAGS = {
    messages.ERROR: "danger",
    messages.SUCCESS: "success",
    messages.INFO: "info",
}

# ==================== Cache ====================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tecnologiafya-cache",
    }
}

# ==================== Divisas (si quisieras exponer algún endpoint legacy) ====================
DOLAR_API_ENDPOINT = config("DOLAR_API_ENDPOINT", default="https://www.dolarapi.com/v1/dolares")

# ==================== Logging (útil p/ ver el scraper en PA) ====================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "divisas": {"handlers": ["console"], "level": "INFO"},
    },
}
