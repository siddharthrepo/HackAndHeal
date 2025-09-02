import os
from pathlib import Path
import environ
import dj_database_url

# Load environment variables from .env file
env = environ.Env()
# environ.Env.read_env()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
env.read_env(os.path.join(BASE_DIR, ".env"), overwrite=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Allow all Replit domains
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'channels',  # For WebSockets
    
    # Custom apps
    'auth_app.apps.AuthAppConfig',
    'consultation_app.apps.ConsultationAppConfig',
    'payment_app.apps.PaymentAppConfig',
    'chat_app.apps.ChatAppConfig',
    'transcription_app.apps.TranscriptionAppConfig',
    'widget_tweaks',
    'corsheaders'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

ROOT_URLCONF = 'chikitsa360.urls'

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

WSGI_APPLICATION = 'chikitsa360.wsgi.application'
ASGI_APPLICATION = 'chikitsa360.asgi.application'

# Database
DEBUG = os.getenv("DEBUG", "True") == "True"
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('PGDATABASE', 'chikitsa360'),
            'USER': os.environ.get('PGUSER', 'postgres'),
            'PASSWORD': os.environ.get('PGPASSWORD', ''),
            'HOST': os.environ.get('PGHOST', 'localhost'),
            'PORT': os.environ.get('PGPORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
    }


CSRF_TRUSTED_ORIGINS = [
    "https://helpless-trixy-siddharthrepo-de886f3f.koyeb.app",
]

ROOT_URLCONF = 'chikitsa360.urls'
WSGI_APPLICATION = 'chikitsa360.wsgi.application'
ASGI_APPLICATION = 'chikitsa360.asgi.application'
# Channel layers for WebSockets
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Password validation
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

CORS_ALLOW_ALL_ORIGINS = True  # or set specific domains
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'origin',
    'x-csrftoken',
    'x-requested-with',
]


# Custom auth user model
AUTH_USER_MODEL = 'auth_app.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'auth_app.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Internationalization
LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URL and redirect URLs
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Email settings
SITE_ID = 1
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Replace with your SMTP host
EMAIL_PORT = 587  # Common for TLS; use 465 for SSL
EMAIL_USE_TLS = True  # Use True if using TLS
EMAIL_USE_SSL = False  # Use False if using TLS
EMAIL_HOST_USER = 'carzone1806@gmail.com'
EMAIL_HOST_PASSWORD = 'onovdkxaixykyzef'
EMAIL_TIMEOUT = 30  # Adjust as needed

# Razorpay settings
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

# settings.py
RAZORPAY_ENABLED = False  # Set to True when you're ready for real payments

# Daily.co settings
# DAILY_API_KEY = env('DAILY_API_KEY')  # Retrieves the variable
DAILY_API_KEY = os.environ.get('DAILY_API_KEY', '')

# Deepgram settings
DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY', '')

# OpenAI settings (for Whisper)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
INSTALLED_APPS += ['csp']

MIDDLEWARE = ['csp.middleware.CSPMiddleware'] + MIDDLEWARE

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ["'self'"],
        'style-src': [
            "'self'", "'unsafe-inline'", '/static/', '/staticfiles/',
            'https://fonts.googleapis.com',
            'https://cdn.tailwindcss.com',
            'https://cdnjs.cloudflare.com',
            'https://use.fontawesome.com'
        ],
        'script-src': [
            "'self'", "'unsafe-inline'", '/static/', '/staticfiles/',
            'https://cdn.tailwindcss.com',
            'https://cdnjs.cloudflare.com',
            'https://use.fontawesome.com',
            'https://unpkg.com',
            'https://*.daily.co'
        ],
        'img-src': [
            "'self'", 'data:', '/static/', '/staticfiles/',
            'https://images.unsplash.com',
            'https://cdn.jsdelivr.net',
            'https://*'
        ],
        'font-src': [
            "'self'", '/static/', '/staticfiles/',
            'https://fonts.gstatic.com',
            'https://cdnjs.cloudflare.com',
            'https://use.fontawesome.com'
        ],
        'connect-src': ["'self'", 'https://*.daily.co'],
        'frame-src': ["'self'", 'https://*.daily.co'],
        'media-src': ["'self'", 'https://*.daily.co'],
    }
}
# Session settings
if DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
    SESSION_COOKIE_SECURE = True  # Only send session cookies over HTTPS
    CSRF_COOKIE_SECURE = True  # Only send CSRF cookies over HTTPS

    # HTTP Strict Transport Security

    # Additional protections
    SECURE_BROWSER_XSS_FILTER = True  # Enable XSS filter in the browser
    SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent content-type sniffing

    # Cookie policy
    SESSION_COOKIE_SAMESITE = 'Lax'  # or 'Strict' if you don't need cross-site usage
    CSRF_COOKIE_SAMESITE = 'Lax'

    # Referrer Policy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

    # If using iframe embedding, control it here
    X_FRAME_OPTIONS = 'DENY'



# CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
# CRISPY_TEMPLATE_PACK = "tailwind"
