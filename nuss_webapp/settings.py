"""
Django settings for nuss_webapp project.
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import dj_database_url


# =========================================================
# BASE DIRECTORY
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# LOAD ENV VARIABLES
# =========================================================
load_dotenv()


# =========================================================
# SECURITY
# =========================================================
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-dev-key'
)

# Trust secure connection proxy headers coming from Cloudflare / Render
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 🛠️ DYNAMIC DEBUG CONFIGURATION
# Debug will evaluate to True ONLY when live on your specific Render domain
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')

if RENDER_HOST == 'nussnhq-portal.onrender.com':
    DEBUG = True
else:
    DEBUG = False


ALLOWED_HOSTS = [
    'nussnhq-portal.onrender.com',
    'nussnhq.com.ng',          # 1. Added root custom domain
    'www.nussnhq.com.ng',      # 2. Added www subdomain
    'localhost',
    '127.0.0.1',
]

# Safeguard to append dynamic system routing fallback hosts automatically if available
if RENDER_HOST and RENDER_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOST)

CSRF_TRUSTED_ORIGINS = [
    'https://nussnhq-portal.onrender.com',
    'https://*.onrender.com',
    'https://nussnhq.com.ng',      # 3. Added secure root custom origin
    'https://www.nussnhq.com.ng',  # 4. Added secure www custom origin
]


# =========================================================
# SECURITY FOR PRODUCTION
# =========================================================
# Even with DEBUG True, keep these fallback placeholders clean
SESSION_COOKIE_SECURE = False if DEBUG else True
CSRF_COOKIE_SECURE = False if DEBUG else True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = False if DEBUG else True


# =========================================================
# APPLICATIONS
# =========================================================
INSTALLED_APPS = [
    # 🛠️ FIXED: Cloudinary Storage must be above staticfiles to catch profile picture paths!
    'cloudinary_storage',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Cloudinary Base Wrapper
    'cloudinary',

    # Local Apps
    'students',
]


# =========================================================
# MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serves static files on live host plans
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================================================
# URLS
# =========================================================
ROOT_URLCONF = 'nuss_webapp.urls'


# =========================================================
# TEMPLATES
# =========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]


# =========================================================
# WSGI
# =========================================================
WSGI_APPLICATION = 'nuss_webapp.wsgi.application'


# =========================================================
# DATABASE
# =========================================================
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =========================================================
# PASSWORD VALIDATORS
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True


# =========================================================
# STATIC & MEDIA FILE BASE CONFIGURATIONS
# =========================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =========================================================
# CLOUDINARY CREDENTIALS
# =========================================================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}


# =========================================================
# 🛠️ UNIFIED PRODUCTION STORAGE ROUTING 
# =========================================================
# Explicitly bound to Cloudinary and WhiteNoise regardless of DEBUG mode
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# 🔑 ADD THIS LINE RIGHT HERE TO FIX THE CLOUDINARY BUILD CRASH:
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =========================================================
# EMAIL CONFIGURATION
# =========================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = (os.getenv('EMAIL_USE_TLS') == 'True')
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASS')

DEFAULT_FROM_EMAIL = f'NUSSNHQ Portal <{EMAIL_HOST_USER}>'


# =========================================================
# AUTH REDIRECTS
# =========================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'student_home'
LOGOUT_REDIRECT_URL = 'login'