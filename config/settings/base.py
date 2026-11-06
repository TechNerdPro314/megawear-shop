from pathlib import Path
import environ
import os
import sentry_sdk

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

ADMIN_SITE_HEADER = "MegaMart CMS"
ADMIN_SITE_TITLE = "MegaMart Admin"
ADMIN_INDEX_TITLE = "Управление магазином"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'apps.importer',
    "import_export",
    "crispy_forms",
    "crispy_bootstrap5",
    "ckeditor",
    "django_filters",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    'apps.info',
    "apps.users",
    "apps.core",
    "apps.catalog",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.promotions",
    "apps.reviews",
    "apps.notifications",
    "apps.seo",
    "apps.comparison",   # добавлено
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

# SEO Settings
SITE_NAME = env("SITE_NAME", default="MegaMart")
SITE_URL = env("SITE_URL", default="https://megamart.ru")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.cart.context_processors.cart_context',
                'apps.seo.context_processors.seo_tags',
                'apps.users.context_processors.unread_notifications',
                'apps.catalog.context_processors.footer_categories',
                'apps.catalog.context_processors.recently_viewed',    # добавлено
                'apps.comparison.context_processors.comparison_count', # добавлено
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
    }
}

AUTH_USER_MODEL = "users.CustomUser"

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

REDIS_URL = f"redis://{env('REDIS_HOST')}:{env('REDIS_PORT')}/1"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

# ==========================================
# ВАРИАНТ Б: ПОЛНОСТЬЮ ИГНОРИРОВАТЬ ПИСЬМА (DUMMY BACKEND)
# ==========================================
# Django будет "проглатывать" все вызовы отправки писем.
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Обязательно задаем заглушку, чтобы Django не падал с ошибкой Invalid address "".
# Даже если письма не отправляются, Django проверяет валидность адреса отправителя.
DEFAULT_FROM_EMAIL = "noreply@megamart.local"

# Настройки для Telegram-уведомлений
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", default="")

# Старые настройки SMTP закомментированы:
# EMAIL_HOST = env("EMAIL_HOST")
# EMAIL_PORT = env.int("EMAIL_PORT")
# EMAIL_HOST_USER = env("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
# EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")

MANAGER_EMAILS = env.list("MANAGER_EMAILS", default=["admin@megamart.ru"])

YOOKASSA_SHOP_ID = env("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = env("YOOKASSA_SECRET_KEY")

if env("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        traces_sample_rate=1.0,
    )

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGES = [
    ('ru', 'Русский'),
]

LOGIN_URL = 'users:login'