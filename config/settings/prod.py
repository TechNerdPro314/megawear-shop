from .base import *

DEBUG = False

# Настройки безопасности для работы за Nginx
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# --- ДОБАВИТЬ ВОТ ЭТО ---
# Список доверенных источников для защиты от CSRF-атак
CSRF_TRUSTED_ORIGINS = [
    "https://megashopnf.ru",
    "https://www.megashopnf.ru",
    "http://megashopnf.ru",
    "http://www.megashopnf.ru",
]