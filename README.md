# 🚀 MegaMart Django — Production Ready Интернет-магазин на Django

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.x-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Celery](https://img.shields.io/badge/Celery-Async-success)

---

# 📌 О проекте

**MegaMart Django** — это современная production-ready архитектура интернет-магазина, разработанная на Django с использованием PostgreSQL, Redis, Celery и Docker.

Проект изначально строится как **масштабируемая eCommerce платформа** под:

* магазины сантехники
* строительные гипермаркеты
* инженерное оборудование
* B2B каталоги поставщиков
* магазины бытовой техники
* high-load ecommerce проекты

Архитектура рассчитана не на учебный CRUD, а на дальнейшее развитие в полноценный коммерческий маркетплейс.

---

# ⚙️ Используемый стек технологий

| Технология              | Назначение            |
| ----------------------- | --------------------- |
| Python 3.12             | Backend               |
| Django 5                | Web framework         |
| PostgreSQL 16           | Основная БД           |
| Redis 7                 | Кэш + брокер задач    |
| Celery                  | Асинхронные задачи    |
| Docker Compose          | Контейнеризация       |
| Gunicorn                | Production WSGI       |
| WhiteNoise              | Раздача static        |
| CKEditor                | RichText редактор     |
| Crispy Forms Bootstrap5 | Красивые формы        |
| Django Import Export    | Импорт/экспорт данных |
| Sentry                  | Мониторинг ошибок     |

---

# 🏗 Архитектура проекта

Проект построен по модульной enterprise-схеме:

```
megamart_django/
│
├── apps/
│   ├── core/              # базовые утилиты
│   ├── users/             # кастомные пользователи
│   ├── catalog/           # каталог товаров
│   ├── cart/              # корзина
│   ├── orders/            # заказы
│   ├── payments/          # платежи
│   ├── promotions/        # купоны/скидки
│   ├── reviews/           # отзывы
│   ├── notifications/     # email/telegram уведомления
│   ├── importer/          # импорт поставщиков
│   └── seo/               # SEO функционал
│
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
│
├── docker/
│   ├── django.Dockerfile
│   ├── celery.Dockerfile
│   ├── docker-compose.yml
│   └── entrypoint.sh
│
├── templates/
├── static/
├── media/
├── requirements/
└── manage.py
```

---

# ✅ Что уже реализовано

## Backend Infrastructure

* Dockerized окружение
* PostgreSQL контейнер
* Redis контейнер
* Celery worker
* Gunicorn server
* Auto migrate + collectstatic в entrypoint
* Health check endpoint `/ht/`

## Django Core

* ENV конфигурация
* Production settings
* Кастомная модель пользователя
* Redis cache
* Celery broker/backend
* SMTP email backend
* YooKassa credentials support
* Sentry support
* WhiteNoise static handling

## Admin CMS

* Полноценная админ панель управления
* Управление товарами
* Управление категориями
* Управление брендами
* Управление импортами поставщиков

## Ecommerce Domain

* Каталог товаров
* SEO поля товаров (SEO backend полностью реализован)
* Галерея товаров
* Атрибуты товаров
* Бренды
* Категории
* Импортная архитектура
* Основа корзины
* Основа заказов

## SEO Backend (Полная реализация)

* ✅ **sitemap.xml** — динамическая генерация карты сайта
* ✅ **robots.txt** — инструкции для поисковых роботов
* ✅ **Canonical URLs** — защита от дублирования контента
* ✅ **Динамические Meta-теги** — Open Graph, Twitter Card
* ✅ **Schema.org JSON-LD** — Product, Category, Brand, Organization, BreadcrumbList, WebSite
* ✅ **Хлебные крошки** — навигация для пользователей и поисковиков
* ✅ **SEO поля в моделях** — `seo_title`, `seo_description`, `seo_keywords` для Category, Brand, Product

---

# 🔐 ENV конфигурация

В корне проекта создаётся файл `.env`:

```env
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=127.0.0.1,localhost

POSTGRES_DB=megamart
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password
EMAIL_USE_TLS=True

YOOKASSA_SHOP_ID=change_me
YOOKASSA_SECRET_KEY=change_me

SENTRY_DSN=

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

SITE_NAME=MegaMart
SITE_URL=http://localhost:8000
```

---

# 🐳 Полная очистка БД и запуск с тестовыми данными

## Способ 1: Через Docker (Рекомендуемый)

### 1. Остановить и удалить все контейнеры

```bash
# Остановить контейнеры
docker compose -f docker/docker-compose.yml down

# Удалить контейнеры, сети и тома (полная очистка БД!)
docker compose -f docker/docker-compose.yml down -v --rmi all
```

> ⚠️ **Внимание!** Команда `-v` удаляет все Docker volumes (данные БД). Это необратимо!

### 2. Пересобрать образы

```bash
docker compose -f docker/docker-compose.yml build --no-cache
```

### 3. Запустить контейнеры

```bash
docker compose -f docker/docker-compose.yml up -d
```

Будут подняты:
* PostgreSQL
* Redis
* Django Web
* Celery Worker

### 4. Создать и применить миграции

```bash
# Создать миграции
docker compose -f docker/docker-compose.yml run --rm -u root web python manage.py makemigrations
# Применить миграции
docker compose -f docker/docker-compose.yml run --rm web python manage.py migrate
```

### 5. Создать суперпользователя

```bash
docker compose -f docker/docker-compose.yml run --rm web python manage.py createsuperuser
```

Введите:
* Email (например: `admin@megamart.ru`)
* Пароль
* Имя (опционально)

### 6. Загрузить тестовые данные

#### Вариант A: Через админку (ручной)

1. Откройте админку: `http://localhost:8000/admin/`
2. Создайте:
   * **Категории**: Смесители, Ванны, Душевые кабины, Унитазы, Мебель для ванной
   * **Бренды**: Grohe, Hansgrohe, Roca, Jacob Delafon, Cersanit
   * **Товары**: Добавьте несколько товаров с изображениями и атрибутами

#### Вариант B: Через manage.py (скрипт)

Создайте файл `apps/catalog/management/commands/load_test_data.py`:

```python
from django.core.management.base import BaseCommand
from apps.catalog.models import Category, Brand, Product, Attribute, ProductAttributeValue

class Command(BaseCommand):
    help = 'Загрузка тестовых данных'

    def handle(self, *args, **kwargs):
        # Создаем категории
        categories = [
            {'name': 'Смесители', 'slug': 'smesiteli'},
            {'name': 'Ванны', 'slug': 'vanny'},
            {'name': 'Душевые кабины', 'slug': 'dushevye-kabiny'},
            {'name': 'Унитазы', 'slug': 'unitazy'},
        ]
        
        for cat_data in categories:
            Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name'], 'is_active': True}
            )
        
        # Создаем бренды
        brands = [
            {'name': 'Grohe', 'slug': 'grohe'},
            {'name': 'Hansgrohe', 'slug': 'hansgrohe'},
            {'name': 'Roca', 'slug': 'roca'},
        ]
        
        for brand_data in brands:
            Brand.objects.get_or_create(
                slug=brand_data['slug'],
                defaults={'name': brand_data['name'], 'is_active': True}
            )
        
        # Создаем атрибуты
        attribute_names = ['Материал', 'Цвет', 'Гарантия', 'Страна производства']
        for attr_name in attribute_names:
            Attribute.objects.get_or_create(
                slug=attr_name.lower().replace(' ', '-'),
                defaults={'name': attr_name, 'is_filterable': True}
            )
        
        # Создаем тестовые товары
        test_products = [
            {
                'name': 'Смеситель Grohe Eurostyle 33456000',
                'slug': 'smesitel-grohe-eurostyle-33456000',
                'sku': '33456000',
                'price': 15990,
                'stock': 25,
                'category_slug': 'smesiteli',
                'brand_slug': 'grohe',
            },
            {
                'name': 'Смеситель Hansgrohe Focus 320',
                'slug': 'smesitel-hansgrohe-focus-320',
                'sku': '31457000',
                'price': 12490,
                'stock': 15,
                'category_slug': 'smesiteli',
                'brand_slug': 'hansgrohe',
            },
            {
                'name': 'Вanna акриловая Roca Adriatic 170x70',
                'slug': 'vanna-akrilovaya-roca-adriatic-170',
                'sku': '33568000',
                'price': 28990,
                'stock': 8,
                'category_slug': 'vanny',
                'brand_slug': 'roca',
            },
        ]
        
        for prod_data in test_products:
            category = Category.objects.get(slug=prod_data['category_slug'])
            brand = Brand.objects.get(slug=prod_data['brand_slug'])
            
            product, created = Product.objects.get_or_create(
                sku=prod_data['sku'],
                defaults={
                    'name': prod_data['name'],
                    'slug': prod_data['slug'],
                    'category': category,
                    'brand': brand,
                    'price': prod_data['price'],
                    'stock': prod_data['stock'],
                    'is_active': True,
                    'short_description': f"Качественный {prod_data['name'].lower()}",
                    'seo_title': f"{prod_data['name']} - Купить в MegaMart",
                    'seo_description': f"Оригинальный {prod_data['name']} по выгодной цене. Доставка по России.",
                }
            )
            
            if created:
                self.stdout.write(f"✓ Создан товар: {product.name}")
            else:
                self.stdout.write(f"⚠ Товар уже существует: {product.name}")
        
        self.stdout.write(self.style.SUCCESS('\n✅ Тестовые данные успешно загружены!'))
```

Запустите команду:

```bash
docker compose -f docker/docker-compose.yml run --rm web python manage.py load_test_data
```

#### Вариант C: Через импорт Excel/CSV

1. Подготовьте файл с товарами (шаблон в `importer/`)
2. В админке: **Importer** → **Загрузить файл**
3. Дождитесь обработки задачи Celery

### 7. Проверить работу

Откройте:
* **Главная**: `http://localhost:8000/`
* **Каталог**: `http://localhost:8000/catalog/`
* **Sitemap**: `http://localhost:8000/sitemap.xml`
* **Robots**: `http://localhost:8000/robots.txt`
* **Админка**: `http://localhost:8000/admin/`

---

## Способ 2: Локальный запуск (без Docker)

### 1. Очистить БД

```bash
# Подключиться к PostgreSQL
psql -U postgres -d megamart

# Удалить все таблицы (внутри psql)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
EXIT;
```

Или удалить базу полностью:

```bash
dropdb -U postgres megamart
createdb -U postgres megamart
```

### 2. Активировать виртуальное окружение

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements/base.txt
```

### 4. Настроить `.env` для локальной работы

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

### 5. Создать миграции и применить

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Создать суперпользователя

```bash
python manage.py createsuperuser
```

### 7. Загрузить тестовые данные

```bash
python manage.py load_test_data
```

### 8. Запустить сервер и Celery

**Терминал 1 (Django):**
```bash
python manage.py runserver
```

**Терминал 2 (Celery):**
```bash
celery -A config worker -l info
```

**Терминал 3 (Celery Beat - для периодических задач):**
```bash
celery -A config beat -l info
```

---

# 📦 Docker контейнеры проекта

После запуска будут работать 4 сервиса:

| Контейнер         | Назначение         | Порт        |
| ----------------- | ------------------ | ----------- |
| `megamart_db`     | PostgreSQL БД      | 5432        |
| `megamart_redis`  | Redis Cache        | 6379        |
| `megamart_web`    | Django приложение  | 8000        |
| `megamart_celery` | Celery async tasks | -           |

---

# 🧪 Проверка состояния проекта

### Health Check

```bash
curl http://localhost:8000/ht/
```

Если все сервисы работают — Django покажет статус:
* `database: working`
* `cache: working`
* `storage: working`

### Проверка SEO

```bash
# Sitemap
curl http://localhost:8000/sitemap.xml

# Robots
curl http://localhost:8000/robots.txt

# Проверка JSON-LD (откройте страницу товара в браузере и посмотрите исходный код)
```

---

# 🔑 Админ панель

Админка доступна по адресу: `http://localhost:8000/admin/`

Через неё можно управлять:
* **Товарами** — добавление, редактирование, SEO поля
* **Категориями** — структура каталога, SEO оптимизация
* **Брендами** — производители, логотипы
* **Импортами** — загрузка товаров от поставщиков
* **Пользователями** — клиенты, менеджеры, администраторы
* **Заказами** — обработка заказов
* **Отзывами** — модерация отзывов

---

# 📈 Текущий статус разработки

**Текущая версия:** `v1_backend_stable`

### Готово:
* ✅ Backend infrastructure
* ✅ Docker environment
* ✅ Admin CMS
* ✅ Product models
* ✅ Importer architecture
* ✅ **SEO Backend (полная реализация)**
* ✅ Cart & Orders foundations
* ✅ Payments integration (YooKassa)
* ✅ Reviews system
* ✅ Notifications (email)

### В разработке:
* ⏳ Storefront frontend (улучшение UI/UX)
* ⏳ Ajax catalog filters
* ⏳ XML/XLS supplier import automation
* ⏳ Telegram notifications
* ⏳ Celery periodic tasks
* ⏳ Elasticsearch search

---

# 🛣 RoadMap развития

### Phase 1: Core (Завершено)
- [x] Docker setup
- [x] PostgreSQL + Redis
- [x] Celery workers
- [x] Admin panel
- [x] Product catalog

### Phase 2: E-commerce (В процессе)
- [x] Cart & Checkout
- [x] Orders management
- [x] Payments (YooKassa)
- [x] Reviews system
- [x] SEO optimization
- [ ] Advanced search (Elasticsearch)
- [ ] Ajax filters & sorting

### Phase 3: Growth
- [ ] Multi-vendor support
- [ ] Loyalty programs
- [ ] Analytics dashboard
- [ ] Mobile app API
- [ ] Production deploy (nginx + gunicorn)
- [ ] CI/CD pipeline

### Phase 4: Scale
- [ ] Microservices architecture
- [ ] Message queue (RabbitMQ)
- [ ] CDN integration
- [ ] AI recommendations
- [ ] Multi-language support

---

# 📞 Поддержка и контакты

При возникновении проблем:

1. Проверьте логи контейнеров:
   ```bash
   docker compose -f docker/docker-compose.yml logs -f web
   docker compose -f docker/docker-compose.yml logs -f celery
   ```

2. Проверьте health endpoint: `http://localhost:8000/ht/`

3. Убедитесь, что все переменные в `.env` настроены правильно

4. Попробуйте полную очистку и пересборку:
   ```bash
   docker compose -f docker/docker-compose.yml down -v --rmi all
   docker compose -f docker/docker-compose.yml build --no-cache
   docker compose -f docker/docker-compose.yml up -d
   ```

---

# 📝 Лицензия

Проект создан для образовательных и коммерческих целей. Используйте на здоровье!

---

**MegaMart Django** — ваш надежный фундамент для ecommerce проектов. 🚀