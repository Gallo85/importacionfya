from pathlib import Path
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-a!j(yus_j5!r9i!(pt0k)a0e&(b_p-b)$ig(b^uq-hq_mc)5h@'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'productos',
    'accounts',
    'facturacion',
    'divisas',
    'django.contrib.humanize',
    'axes',  # 🔒 Protección contra fuerza bruta
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # 🔒 Middleware para bloquear intentos de login fallidos
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Primero, la autenticación normal de Django
    'axes.backends.AxesBackend',  # Luego, la seguridad de Axes
]


ROOT_URLCONF = 'Importaciones_fya.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'Importaciones_fya.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'importacion_fya',  # Nombre de la base de datos en MySQL
        'USER': 'root',  # Usuario de MySQL
        'PASSWORD': 'Brunito_2020',  # Contraseña de MySQL
        'HOST': 'localhost',  # Para MySQL local, en PythonAnywhere será diferente
        'PORT': '3306',  # Puerto de MySQL (por defecto)
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'accounts.Usuario'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Configuración del Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = config('EMAIL_HOST_USER')  # Debe estar en el .env
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # Debe estar en el .env
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# API para conversión de divisas
DOLAR_API_ENDPOINT = config('DOLAR_API_ENDPOINT', default='https://api.exchangeratesapi.io/latest')

# 🔒 Configuración de Django Axes para bloquear intentos de login fallidos
AXES_FAILURE_LIMIT = 5  # Número de intentos antes de bloquear
AXES_COOLOFF_TIME = 5  # Tiempo de espera en horas antes de permitir un nuevo intento
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'  # Página personalizada cuando un usuario es bloqueado
AXES_RESET_ON_SUCCESS = True  # 🔒 Reinicia los intentos fallidos si el usuario ingresa correctamente




