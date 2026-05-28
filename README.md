# MarketHub

A full-featured Django marketplace — buyers browse and purchase products, vendors manage their storefronts, admins approve sellers. Built to teach every major Django concept from the ground up, with real production patterns.

> **Who this README is for:** Complete beginners who want to understand *why* each file exists, *what* each concept does, and *how* senior engineers think about Django projects. Every section has a plain-English explanation, a working code example, and a link to the official docs.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Setup & Installation](#2-setup--installation)
3. [How Django Works — The Big Picture](#3-how-django-works--the-big-picture)
4. [Settings & Configuration](#4-settings--configuration)
5. [Apps Architecture & AppConfig](#5-apps-architecture--appconfig)
6. [The `__init__.py` File — Why Every Package Needs It](#6-the-initpy-file--why-every-package-needs-it)
7. [Models & ORM](#7-models--orm)
8. [Abstract Base Models](#8-abstract-base-models)
9. [Custom User Model](#9-custom-user-model)
10. [Migrations](#10-migrations)
11. [Django Forms](#11-django-forms)
12. [Service Layer Pattern](#12-service-layer-pattern)
13. [Views](#13-views)
14. [URLs & Routing](#14-urls--routing)
15. [Templates](#15-templates)
16. [Middleware](#16-middleware)
17. [Context Processors](#17-context-processors)
18. [Static & Media Files](#18-static--media-files)
19. [Admin Interface](#19-admin-interface)
20. [Authentication & Authorization](#20-authentication--authorization)
21. [Django REST Framework (DRF)](#21-django-rest-framework-drf)
22. [JWT Authentication](#22-jwt-authentication)
23. [Filtering, Search & Ordering](#23-filtering-search--ordering)
24. [Signals](#24-signals)
25. [Celery & Async Tasks](#25-celery--async-tasks)
26. [WSGI & ASGI](#26-wsgi--asgi)
27. [Environment Variables](#27-environment-variables)
28. [Tech Stack](#28-tech-stack)
29. [Senior Engineer Tips & Best Practices](#29-senior-engineer-tips--best-practices)

---

## 1. Project Structure

```
markethub/
├── config/                        # Django project configuration (not an app)
│   ├── __init__.py                # Makes config a Python package; loads Celery
│   ├── celery.py                  # Celery application instance
│   ├── settings/
│   │   ├── base.py                # Settings shared across ALL environments
│   │   ├── development.py         # Dev-only overrides (DEBUG=True, etc.)
│   │   └── production.py          # Prod-only overrides (security, caching)
│   ├── urls.py                    # Root URL dispatcher
│   ├── asgi.py                    # ASGI entry point (async servers, WebSockets)
│   └── wsgi.py                    # WSGI entry point (traditional sync servers)
│
├── apps/                          # All local Django apps live here
│   ├── __init__.py                # Makes apps/ a Python package
│   ├── core/                      # Shared utilities used by all other apps
│   │   ├── __init__.py
│   │   ├── apps.py                # App registration config
│   │   ├── models.py              # TimeStamped abstract base model
│   │   ├── middleware.py          # RequestTimingMiddleware
│   │   └── context_processors.py  # Global cart count injected into templates
│   └── accounts/                  # User registration, login, vendor profiles
│       ├── __init__.py
│       ├── apps.py                # App registration config
│       ├── models.py              # User + VendorProfile models
│       ├── forms.py               # RegisterForm (HTML form validation)
│       ├── views.py               # register, login_view, logout_view
│       ├── services.py            # Business logic (register_user, become_vendor)
│       ├── urls.py                # accounts/ URL patterns
│       └── migrations/            # Auto-generated database schema changes
│           └── 0001_initial.py
│
├── templates/                     # Global HTML templates
├── static/                        # CSS, JS, images (project-level)
├── manage.py                      # Django's CLI tool (run commands here)
├── requirements.txt               # All Python dependencies
└── .env                           # Secret config values — NEVER commit this
```

> **Beginner tip:** The `config/` folder is what `django-admin startproject` creates. The `apps/` folder is where you put all the features you build. Keep them separate.

---

## 2. Setup & Installation

Follow these steps exactly, in order.

```bash
# Step 1 — Get the code
git clone <repo-url>
cd markethub

# Step 2 — Create an isolated Python environment
# A virtual environment keeps this project's packages separate from other projects
python -m venv .venv

# Step 3 — Activate it (you must do this every time you open a new terminal)
.venv\Scripts\activate        # Windows PowerShell
source .venv/bin/activate     # macOS / Linux

# Step 4 — Install all dependencies
pip install -r requirements.txt

# Step 5 — Create the .env file (copy this exactly, then change SECRET_KEY)
# This file holds secrets that must never go into git
SECRET_KEY=replace-this-with-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://127.0.0.1:6379

# Step 6 — Create the database tables
python manage.py migrate

# Step 7 — Create an admin login (follow the prompts)
python manage.py createsuperuser

# Step 8 — Start the server
python manage.py runserver
# Visit http://127.0.0.1:8000 in your browser
# Admin panel: http://127.0.0.1:8000/admin/

# Step 9 (optional) — Start a Celery worker for background tasks
# Open a second terminal, activate the venv, then:
celery -A config worker -l info
```

> **Windows PowerShell note:** If you need to set the settings module manually:
> ```powershell
> $env:DJANGO_SETTINGS_MODULE = 'config.settings.development'
> python manage.py runserver
> ```

---

## 3. How Django Works — The Big Picture

Before diving into individual files, here is how a single web request flows through Django:

```
Browser sends:  GET /accounts/login/
                        │
                   manage.py / wsgi.py
                        │
                   Django loads settings
                        │
              ┌─────────▼──────────┐
              │     MIDDLEWARE      │  ← runs top-to-bottom on the way IN
              │  SecurityMiddleware │
              │  SessionMiddleware  │
              │  RequestTiming...   │
              └─────────┬──────────┘
                        │
                   config/urls.py   ← finds: path("accounts/", include(...))
                        │
               accounts/urls.py    ← finds: path("login/", views.login_view)
                        │
                  views.login_view  ← your Python function runs here
                        │
                  renders template  ← accounts/login.html extends base.html
                        │
              ┌─────────▼──────────┐
              │     MIDDLEWARE      │  ← runs bottom-to-top on the way OUT
              └─────────┬──────────┘
                        │
               Browser receives HTML response
```

Every file you create plugs into one step of this pipeline.

---

## 4. Settings & Configuration

### What is it?

Settings are Django's control panel — they tell Django which database to use, which apps are installed, how templates are found, and hundreds of other things.

### Why split into multiple files?

A single `settings.py` works but creates a common problem: you need `DEBUG=True` in development and `DEBUG=False` in production. If you forget to change it before deploying, your site leaks error details to attackers. The split-settings pattern solves this permanently.

```
config/settings/
├── base.py          ← everything both environments share
├── development.py   ← imports base, then overrides for local dev
└── production.py    ← imports base, then overrides for live server
```

```python
# config/settings/base.py  ← shared by everyone
import environ
from pathlib import Path

# BASE_DIR points to the markethub/ root folder
# Path(__file__) = .../config/settings/base.py
# .parent        = .../config/settings/
# .parent.parent = .../config/
# .parent.parent.parent = .../markethub/   ← this is BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))   # tells environ: DEBUG should be a bool, default False
environ.Env.read_env(BASE_DIR / '.env')  # reads the .env file from the project root

SECRET_KEY    = env('SECRET_KEY')        # reads SECRET_KEY from .env as a string
DEBUG         = env('DEBUG')             # reads DEBUG from .env, converts to True/False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])
DATABASES     = {'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')}
```

```python
# config/settings/development.py  ← only used locally
from .base import *   # inherits EVERYTHING from base.py

DEBUG = True          # override: always show errors in dev
# You can add dev-only tools here, e.g. django-debug-toolbar
```

```python
# config/settings/production.py  ← only used on live server
from .base import *

DEBUG = False                  # never show error details in production
SECURE_SSL_REDIRECT = True     # force HTTPS
SESSION_COOKIE_SECURE = True   # cookie only sent over HTTPS
CSRF_COOKIE_SECURE = True
```

### How Django knows which settings file to use

[`manage.py`](manage.py) sets the default:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
```

`setdefault` means "use this value *unless* the environment variable is already set". On your server, you set `DJANGO_SETTINGS_MODULE=config.settings.production` in the environment, and Django picks that up automatically.

[`config/wsgi.py`](config/wsgi.py) and [`config/asgi.py`](config/asgi.py) default to production because those files are only used by web servers (Gunicorn/Uvicorn), never by `manage.py`:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
```

**Key settings at a glance:**

| Setting | What it controls |
|---|---|
| `INSTALLED_APPS` | Which apps Django knows about |
| `MIDDLEWARE` | Request/response processors, run in order |
| `DATABASES` | Which database to connect to |
| `TEMPLATES` | Where templates live, what context processors run |
| `AUTH_USER_MODEL` | Which model represents a logged-in user |
| `REST_FRAMEWORK` | DRF-wide defaults for auth, permissions, pagination |
| `STATIC_URL / MEDIA_URL` | URL prefixes for CSS/JS and user uploads |

**Docs:** https://docs.djangoproject.com/en/6.0/ref/settings/

---

## 5. Apps Architecture & AppConfig

### What is a Django app?

A Django **app** is a self-contained Python package for one feature area. The project is the whole website; apps are the rooms inside it.

```
apps/
├── core/        ← shared plumbing (base models, middleware, context processors)
├── accounts/    ← who users are and how they log in
├── catalog/     ← products and categories
├── orders/      ← shopping cart and purchases
├── reviews/     ← ratings and written reviews
└── notifications/ ← alerts for buyers and vendors
```

### AppConfig — registering an app properly

Every app has an [`apps.py`] that tells Django its full Python path. This is also where you wire up signals.

```python
# apps/accounts/apps.py
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = 'apps.accounts'                          # must match the path in INSTALLED_APPS
    default_auto_field = 'django.db.models.BigAutoField'  # default primary key type

    def ready(self):
        # Import signals here so they connect when Django starts
        import apps.accounts.signals  # noqa: F401
```

```python
# apps/core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'apps.core'
    default_auto_field = 'django.db.models.BigAutoField'
```

Registered in `base.py`:

```python
INSTALLED_APPS = [
    # Django built-ins (always first)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party packages
    'rest_framework',
    'django_filters',
    'django_extensions',
    # Your apps
    'apps.core',
    'apps.accounts',
    'apps.catalog',
    'apps.orders',
    'apps.reviews',
    'apps.notifications',
]
```

### Standard app layout

```
apps/accounts/
├── __init__.py     ← makes this a Python package (required)
├── apps.py         ← AppConfig (registers the app with Django)
├── models.py       ← database table definitions
├── forms.py        ← HTML form validation
├── views.py        ← handles HTTP requests
├── services.py     ← business logic (separate from views)
├── urls.py         ← URL patterns for this app
├── admin.py        ← admin panel registration
├── serializers.py  ← DRF: converts models to/from JSON
├── signals.py      ← react to model events
├── filters.py      ← DRF: query parameter filters
└── migrations/     ← auto-generated database migrations
    ├── __init__.py
    └── 0001_initial.py
```

**Docs:** https://docs.djangoproject.com/en/6.0/ref/applications/

---

## 6. The `__init__.py` File — Why Every Package Needs It

### What is it?

An `__init__.py` is an empty (or nearly empty) file that tells Python: *"this folder is a package — you can import from it."*

Without it, `from apps.accounts.models import User` fails with `ModuleNotFoundError`, even if the files exist.

```
apps/
├── __init__.py          ← without this, Python can't import from apps/
├── accounts/
│   ├── __init__.py      ← without this, Python can't import from apps/accounts/
│   └── models.py
└── core/
    ├── __init__.py
    └── models.py
```

### The one `__init__.py` that does real work

[`config/__init__.py`](config/__init__.py) does more than mark a package — it loads Celery when Django starts:

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ("celery_app",)
```

**Why?** Celery's `@shared_task` decorator needs the Celery app to be initialised before any task module is imported. Putting this import here ensures that happens automatically, in the right order, every time Django starts.

> **Beginner tip:** You will almost never write anything in `__init__.py`. Its job is usually just to exist. The `config/__init__.py` is the rare exception.

---

## 7. Models & ORM

### What is a model?

A **model** is a Python class that maps directly to a database table. Each class attribute is a column. Django's ORM (Object-Relational Mapper) lets you query and manipulate the database using Python instead of raw SQL.

```python
# apps/catalog/models.py  (example — to be built)
from django.db import models
from apps.core.models import TimeStamped  # inherits created_at + updated_at
from apps.accounts.models import User

class Category(TimeStamped):
    name   = models.CharField(max_length=200)   # VARCHAR(200) column
    slug   = models.SlugField(unique=True)       # URL-safe name, must be unique
    parent = models.ForeignKey(
        'self',                   # self-referencing: a category can have a parent
        null=True, blank=True,    # null=True → column can be NULL in DB
                                  # blank=True → field is optional in forms
        related_name='children',  # access subcategories via category.children.all()
        on_delete=models.SET_NULL # if parent deleted, set this field to NULL
    )

    class Meta:
        verbose_name_plural = 'categories'  # fix the admin label
        ordering = ['name']                 # default sort order

    def __str__(self):
        return self.name   # shown in admin and shell


class Product(TimeStamped):
    seller      = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='products')  # user.products.all()
    category    = models.ForeignKey(Category, on_delete=models.PROTECT)
                  # PROTECT = refuse to delete a category that still has products
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(unique=True)
    description = models.TextField()
    price       = models.DecimalField(max_digits=10, decimal_places=2)
                  # always use DecimalField for money — FloatField has rounding errors
    stock       = models.PositiveIntegerField(default=0)
    image       = models.ImageField(upload_to='products/', blank=True)

    def __str__(self):
        return self.name
```

### ORM query cheatsheet

```python
# CREATE
product = Product.objects.create(name='Keyboard', price=49.99, ...)

# READ — single object (raises 404 if missing)
from django.shortcuts import get_object_or_404
product = get_object_or_404(Product, slug='mechanical-keyboard')

# READ — list with filtering
Product.objects.filter(category__slug='electronics', price__lte=100)
#                      ^^^ double underscore = JOIN        ^^^ lte = less than or equal

# READ — avoid N+1 queries (critical for performance)
# BAD: this runs 1 query for products + 1 per product to get seller (N+1 problem)
products = Product.objects.all()
for p in products:
    print(p.seller.email)   # ← hits the DB for every single product!

# GOOD: one query with a JOIN
products = Product.objects.select_related('seller', 'category')
# select_related  → for ForeignKey / OneToOne (SQL JOIN)
# prefetch_related → for ManyToMany / reverse FK (separate query, then Python join)
products = Product.objects.prefetch_related('reviews')

# AGGREGATE
from django.db.models import Avg, Count
Product.objects.annotate(
    avg_rating=Avg('reviews__rating'),
    review_count=Count('reviews')
)

# UPDATE — only save changed fields (faster, avoids race conditions)
product.price = 39.99
product.save(update_fields=['price'])

# DELETE
product.delete()
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/db/models/
**ORM query reference:** https://docs.djangoproject.com/en/6.0/ref/models/querysets/

---

## 8. Abstract Base Models

### What is it?

An **abstract model** is a model that never creates its own database table. Its only job is to be inherited by other models, giving them shared fields.

### The `TimeStamped` model

Every table in MarketHub should know *when a row was created* and *when it was last changed*. Instead of adding `created_at` and `updated_at` to every model manually, they inherit from `TimeStamped`:

```python
# apps/core/models.py
from django.db import models

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # auto_now_add=True → set automatically when the row is first created, never changed
    # db_index=True     → adds a database index so ORDER BY created_at is fast

    updated_at = models.DateTimeField(auto_now=True)
    # auto_now=True → updated automatically every time .save() is called

    class Meta:
        abstract = True  # ← the magic line: no table is created for TimeStamped itself
```

### How to use it

```python
# Any model can now inherit TimeStamped
class Product(TimeStamped):       # gains created_at + updated_at automatically
    name = models.CharField(...)

class Order(TimeStamped):         # same fields, no duplication
    buyer = models.ForeignKey(...)

class Notification(TimeStamped):  # same here
    message = models.TextField()
```

The resulting database columns look like:

```sql
-- products table
id          INTEGER  PRIMARY KEY
name        VARCHAR(255)
created_at  TIMESTAMP  -- from TimeStamped
updated_at  TIMESTAMP  -- from TimeStamped
...
```

> **Senior tip:** Always put `created_at` and `updated_at` on every table from day one. Debugging production issues without timestamps is painful — you can't answer "when did this happen?" without them. Adding them retroactively is a migration headache on large tables.

**Docs:** https://docs.djangoproject.com/en/6.0/topics/db/models/#abstract-base-classes

---

## 9. Custom User Model

### Why not use Django's built-in User?

Django ships with a `User` model, but it uses `username` as the login field. Most modern apps use `email` as the login. Switching after your first migration is a nightmare — it requires rewriting all your foreign keys.

**The rule: always create a custom User model before running your first migration.**

### MarketHub's User model

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStamped

class User(AbstractUser, TimeStamped):
    # Role choices: a clean way to represent a fixed set of string values
    class Role(models.TextChoices):
        BUYER  = "buyer",  "Buyer"   # (db_value, human_label)
        VENDOR = "vendor", "Vendor"
        ADMIN  = "admin",  "Admin"

    email       = models.EmailField(unique=True)   # override: must be unique
    role        = models.CharField(
                      max_length=10,
                      choices=Role.choices,        # validates only these values
                      default=Role.BUYER           # new users are buyers by default
                  )
    is_verified = models.BooleanField(default=False)  # email verification flag

    USERNAME_FIELD  = "email"      # "email" is the login credential (not username)
    REQUIRED_FIELDS = ["username"] # createsuperuser still asks for username
                                   # AbstractUser requires it; we keep it for compatibility

    @property
    def is_vendor(self):
        # A Python property — accessed like an attribute, not a method
        # Usage: if user.is_vendor: ...
        return self.role == self.Role.VENDOR

    def __str__(self):
        return self.email


class VendorProfile(TimeStamped):
    # OneToOneField: each vendor has exactly one profile, each profile belongs to one vendor
    user        = models.OneToOneField(User, on_delete=models.CASCADE,
                                       related_name="vendor")  # access via user.vendor
    store_name  = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)  # URL: /vendors/my-store/
    bio         = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)  # admin must approve before selling
    rating      = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    # denormalised average: stored here so we don't recalculate on every page load

    def __str__(self):
        return self.store_name
```

Linked in settings:

```python
# config/settings/base.py
AUTH_USER_MODEL = 'accounts.User'

# Auth redirects
LOGIN_URL          = 'accounts:login'
LOGIN_REDIRECT_URL = 'catalog:home'
LOGOUT_REDIRECT_URL = 'catalog:home'
```

> **Senior tip:** Use `TextChoices` (or `IntegerChoices`) instead of raw strings for roles/statuses. It gives you auto-complete in your IDE, prevents typos, and keeps all valid values in one place. Access them as `User.Role.VENDOR` — never as the raw string `"vendor"`.

**Docs:** https://docs.djangoproject.com/en/6.0/topics/auth/customizing/#substituting-a-custom-user-model

---

## 10. Migrations

### What is a migration?

When you add, change, or remove a model field, the database doesn't know about it automatically. A **migration** is a Python file that describes those schema changes. Django runs migrations to keep the database in sync with your models.

### The migration workflow

```bash
# 1. You edit models.py (add a field, change max_length, etc.)

# 2. Generate a migration file
python manage.py makemigrations accounts
# → apps/accounts/migrations/0002_user_add_phone_number.py (auto-generated)

# 3. Apply the migration to the database
python manage.py migrate

# 4. Check which migrations have been applied
python manage.py showmigrations
```

### What a generated migration looks like

[`apps/accounts/migrations/0001_initial.py`](apps/accounts/migrations/0001_initial.py) — auto-generated when we first ran `makemigrations accounts`:

```python
class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        # ↑ our User depends on Django's auth tables — must run first
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                # All fields listed here — including those from AbstractUser and TimeStamped
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(choices=[...], default='buyer', max_length=10)),
                ('is_verified', models.BooleanField(default=False)),
                # ... more fields from AbstractUser ...
            ],
        ),
        migrations.CreateModel(name='VendorProfile', fields=[...]),
    ]
```

### Why the database was reset

When we first ran `migrate`, Django applied all its built-in migrations (for `auth`, `admin`, `sessions`) using the default `auth.User`. Then we added our custom `accounts.User`. Django refuses to run because the admin tables were built against the wrong user model — the migration history was inconsistent.

**Fix:** delete `db.sqlite3` and run `migrate` from scratch. In PostgreSQL production, you would handle this with a proper migration squash instead of deleting.

> **Senior tip:** Never edit a migration file that has already been applied in production. Instead, create a new migration that reverses or continues from it. Editing applied migrations breaks the history checksum and causes `InconsistentMigrationHistory` errors for every developer on your team.

**Docs:** https://docs.djangoproject.com/en/6.0/topics/migrations/

---

## 11. Django Forms

### What is a form?

A Django **form** is a Python class that:
1. Defines which fields appear in an HTML form
2. Validates submitted data (required fields, email format, password match, etc.)
3. Converts raw string inputs to the correct Python types

```python
# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    # UserCreationForm already has:
    #   - password1 (new password)
    #   - password2 (confirm password)
    #   - built-in validation that both passwords match
    #   - password strength checks

    class Meta:
        model  = User
        fields = ["email", "username", "role", "password1", "password2"]
        # These fields appear in the rendered HTML form, in this order
```

### How a form works in a view

```python
# The pattern used in views.py:
def register(request):
    form = RegisterForm(request.POST or None)
    # request.POST or None:
    #   - On GET request:  request.POST is empty → None → form is unbound (blank)
    #   - On POST request: request.POST has data → form is bound (filled in)

    if form.is_valid():
        # is_valid() runs all validators and returns True only if everything passes
        user = services.register_user(
            email    = form.cleaned_data["email"],
            # cleaned_data gives you the VALIDATED, type-converted value
            # (raw strings have been checked for format, stripped of whitespace, etc.)
            username = form.cleaned_data["username"],
            password = form.cleaned_data["password1"],
            role     = form.cleaned_data["role"],
        )
        login(request, user)
        return redirect("catalog:home")

    # If form is invalid: re-render with errors shown
    return render(request, "accounts/register.html", {"form": form})
```

### Rendering the form in a template

```html
<!-- templates/accounts/register.html -->
<form method="post">
    {% csrf_token %}   {# required: prevents Cross-Site Request Forgery attacks #}
    {{ form.as_p }}    {# renders each field wrapped in <p> tags with labels + errors #}
    <button type="submit">Register</button>
</form>
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/forms/

---

## 12. Service Layer Pattern

### What is it?

A **service layer** is a `services.py` file containing plain Python functions that hold your business logic — separate from views (HTTP handling) and models (data structure).

### Why does this matter?

Without a service layer, business logic creeps into views. When you later need to run the same logic from a management command, a Celery task, or an API endpoint, you end up copying code. Services are reusable.

```python
# apps/accounts/services.py
from django.db import transaction
from django.utils.text import slugify
from .models import User, VendorProfile

@transaction.atomic
def register_user(*, email, username, password, role=User.Role.BUYER):
    # @transaction.atomic: if ANYTHING in this function raises an exception,
    # ALL database writes are rolled back — the operation is all-or-nothing

    # * in the signature = keyword-only arguments
    # You MUST call this as: register_user(email=x, username=y, password=z)
    # This prevents mistakes like: register_user("john@test.com", "john", "pass")

    user = User(email=email, username=username, role=role)
    user.set_password(password)   # hashes the password using Django's hasher
                                   # NEVER store passwords as plain text
    user.save()
    return user


@transaction.atomic
def become_vendor(*, user, store_name, bio=""):
    user.role = User.Role.VENDOR
    user.save(update_fields=["role"])
    # update_fields=["role"]: only sends UPDATE SET role=... to the database
    # Without this, Django sends UPDATE SET every_column=... which:
    #   1. is slower
    #   2. can overwrite changes made by another request (race condition)

    return VendorProfile.objects.create(
        user       = user,
        store_name = store_name,
        slug       = slugify(store_name),  # "My Cool Store" → "my-cool-store"
        bio        = bio,
    )
```

### The rule of thumb

| Code type | Where it goes |
|---|---|
| HTTP request/response handling, redirects | `views.py` |
| Data validation, form rendering | `forms.py` |
| Business rules, database writes, transactions | `services.py` |
| Database table structure | `models.py` |
| Database reads / query helpers | `selectors.py` (or `models.py`) |

> **Senior tip:** Keep views thin. A view should do three things: parse the request, call a service, return a response. If your view has `if/elif/else` chains and multiple `.save()` calls, extract that logic into a service function. Views that call services are easy to test; views with embedded business logic are not.

---

## 13. Views

### What is a view?

A **view** is a Python function (or class) that receives an HTTP request and returns an HTTP response. It is the bridge between the URL, the business logic, and the template.

### Function-Based Views (FBVs)

Simple, explicit, best for custom one-off endpoints:

```python
# apps/accounts/views.py
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .forms import RegisterForm
from . import services

def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = services.register_user(
            email    = form.cleaned_data["email"],
            username = form.cleaned_data["username"],
            password = form.cleaned_data["password1"],
            role     = form.cleaned_data["role"],
        )
        login(request, user)           # log the user in immediately after registering
        return redirect("catalog:home")
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    # AuthenticationForm handles: does this user exist? is the password correct?
    if form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next", "catalog:home"))
        # "next": if the user was redirected to login from a protected page,
        # send them back there after logging in
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("catalog:home")
```

### Class-Based Views (CBVs)

Less boilerplate for standard CRUD operations. Django provides built-in generics:

```python
# apps/catalog/views.py  (example — to be built)
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Product

class ProductListView(ListView):
    model                = Product
    template_name        = 'catalog/product_list.html'
    context_object_name  = 'products'  # name used in template: {% for product in products %}
    paginate_by          = 20          # auto-paginates: adds page_obj to context

    def get_queryset(self):
        qs = super().get_queryset().select_related('category', 'seller')
        q  = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)  # case-insensitive search
        return qs


class SellerDashboard(LoginRequiredMixin, UserPassesTestMixin, ListView):
    # LoginRequiredMixin: redirects to LOGIN_URL if user is not authenticated
    # UserPassesTestMixin: calls test_func(); returns 403 if it returns False

    def test_func(self):
        return self.request.user.is_vendor   # only vendors can access this
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/class-based-views/

---

## 14. URLs & Routing

### How Django finds your view

Django reads `ROOT_URLCONF = 'config.urls'` from settings, then matches the incoming URL against patterns in order. The first match wins.

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # include() hands off to another urls.py file
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('',          include('apps.catalog.urls',  namespace='catalog')),
    path('orders/',   include('apps.orders.urls',   namespace='orders')),
    path('api/v1/',   include('apps.catalog.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# static(...) only adds the media URL in DEBUG mode — never in production
```

```python
# apps/accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"   # namespace: use {% url 'accounts:login' %} in templates

urlpatterns = [
    path("register/", views.register,     name="register"),
    path("login/",    views.login_view,   name="login"),
    path("logout/",   views.logout_view,  name="logout"),
]
```

### URL patterns and converters

```python
path('products/<slug:slug>/', views.detail)   # /products/mechanical-keyboard/
path('orders/<int:pk>/',      views.order)    # /orders/42/
path('search/',               views.search)  # /search/?q=keyboard (query params in view)
```

### Reversing URLs

Never hardcode URLs in Python or templates. Use `reverse()` and `{% url %}` so that renaming a URL only requires changing `urls.py`:

```python
# In Python
from django.urls import reverse
url = reverse('accounts:login')  # → '/accounts/login/'
url = reverse('catalog:product-detail', kwargs={'slug': 'keyboard'})
```

```html
<!-- In templates -->
<a href="{% url 'accounts:register' %}">Sign up</a>
<a href="{% url 'catalog:product-detail' slug=product.slug %}">View</a>
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/http/urls/

---

## 15. Templates

### What is a template?

A template is an HTML file with special `{% %}` tags and `{{ }}` variables that Django fills in before sending the page to the browser.

### Template inheritance — the most important pattern

Define the page structure once in `base.html`, then override only what changes per page.

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{% block title %}MarketHub{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
</head>
<body>
    <nav>
        <a href="{% url 'catalog:home' %}">Home</a>
        {% if user.is_authenticated %}
            <a href="{% url 'accounts:logout' %}">Logout ({{ user.email }})</a>
            <span>Cart: {{ cart_count }}</span>   {# injected by context processor #}
        {% else %}
            <a href="{% url 'accounts:login' %}">Login</a>
            <a href="{% url 'accounts:register' %}">Register</a>
        {% endif %}
    </nav>

    {# Flash messages from Django's messages framework #}
    {% for message in messages %}
        <div class="alert alert-{{ message.tags }}">{{ message }}</div>
    {% endfor %}

    <main>
        {% block content %}{% endblock %}  {# child templates put content here #}
    </main>
</body>
</html>
```

```html
<!-- apps/accounts/templates/accounts/login.html -->
{% extends 'base.html' %}

{% block title %}Login — MarketHub{% endblock %}

{% block content %}
<h1>Log In</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Log In</button>
</form>
<p>No account? <a href="{% url 'accounts:register' %}">Register</a></p>
{% endblock %}
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/templates/

---

## 16. Middleware

### What is middleware?

Middleware is code that runs on **every single request and response** — before the view receives the request, and after the view returns a response. Think of it as a pipeline of filters.

```
Request IN  → [Security] → [Session] → [CSRF] → [Auth] → [Timing] → View
Response OUT ← [Security] ← [Session] ← [CSRF] ← [Auth] ← [Timing] ← View
```

### MarketHub's custom middleware

```python
# apps/core/middleware.py
import time
import logging

log = logging.getLogger(__name__)

class RequestTimingMiddleware:
    def __init__(self, get_response):
        # Called ONCE when Django starts. Store the next middleware/view callable.
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)   # ← everything else runs here
                                                 # (all inner middleware + the view)

        duration = time.time() - start_time
        if duration > 1.0:
            # Only log requests that are unusually slow — not every request
            log.warning("SLOW %s %s %.2fs", request.method, request.path, duration)

        response["X-Response-Time"] = f"{duration:.3f}"
        # Adds a custom header — useful for debugging in browser DevTools
        return response
```

Registered in `base.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',     # HTTPS, HSTS
    'django.contrib.sessions.middleware.SessionMiddleware',  # session support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',         # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # attaches request.user
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.RequestTimingMiddleware',      # our custom one — last
]
```

> **Senior tip:** The order of middleware matters. `AuthenticationMiddleware` must come before any middleware that uses `request.user`. `SessionMiddleware` must come before `AuthenticationMiddleware`. If you add custom middleware that depends on `request.user`, place it *after* `AuthenticationMiddleware` in the list.

**Docs:** https://docs.djangoproject.com/en/6.0/topics/http/middleware/

---

## 17. Context Processors

### What is a context processor?

A context processor is a function that runs on every request and adds variables to the template context globally — so every template can use them without the view passing them explicitly.

```python
# apps/core/context_processors.py
def cart(request):
    from apps.orders.selectors import cart_item_count
    # Why the import is here, not at the top of the file:
    # Django imports context_processors.py before apps are fully loaded.
    # Putting the import inside the function avoids circular import errors.
    return {
        "cart_count": cart_item_count(request.user) if request.user.is_authenticated else 0
    }
    # Every template now has {{ cart_count }} available automatically
```

Registered in `base.py`:

```python
TEMPLATES = [{
    ...
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',  # adds request to templates
            'django.contrib.auth.context_processors.auth',  # adds user, perms
            'django.contrib.messages.context_processors.messages',
            'apps.core.context_processors.cart',  # ← our custom one
        ],
    },
}]
```

**Docs:** https://docs.djangoproject.com/en/6.0/ref/templates/api/#built-in-template-context-processors

---

## 18. Static & Media Files

### Static files (your code's assets)

CSS, JavaScript, and images that ship with the project.

```python
STATIC_URL       = '/static/'              # URL prefix: /static/css/main.css
STATIC_ROOT      = BASE_DIR / 'staticfiles' # where collectstatic copies files for production
STATICFILES_DIRS = [BASE_DIR / 'static']   # extra directories to search
```

```bash
# Development: Django serves them automatically (no extra setup)
# Production: run this first, then serve staticfiles/ with nginx
python manage.py collectstatic
```

### Media files (user uploads)

Files uploaded by users (product images, avatars).

```python
MEDIA_URL  = '/media/'          # URL prefix: /media/products/keyboard.jpg
MEDIA_ROOT = BASE_DIR / 'media' # where uploaded files are stored on disk
```

```python
# config/urls.py — serve media files in development only
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

```html
{% load static %}
<img src="{% static 'images/logo.png' %}">        <!-- static file -->
<img src="{{ product.image.url }}">                <!-- user upload -->
```

> **Senior tip:** Never serve user uploads from the same domain as your application in production. Use a CDN or object storage (AWS S3, Cloudflare R2). Serving untrusted files through your app server is a security and performance risk. In production, use `django-storages` to redirect uploads to S3 automatically.

**Docs:** https://docs.djangoproject.com/en/6.0/howto/static-files/

---

## 19. Admin Interface

Django auto-generates a full CRUD UI for every registered model. Go to `/admin/` after `createsuperuser`.

```python
# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VendorProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Extend Django's built-in UserAdmin so password hashing still works
    list_display  = ('email', 'username', 'role', 'is_verified', 'is_staff')
    list_filter   = ('role', 'is_verified', 'is_staff')
    search_fields = ('email', 'username')
    # Add our custom fields to the edit form
    fieldsets = UserAdmin.fieldsets + (
        ('MarketHub', {'fields': ('role', 'is_verified')}),
    )


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display  = ('store_name', 'user', 'is_approved', 'rating', 'created_at')
    list_filter   = ('is_approved',)
    search_fields = ('store_name', 'user__email')
    prepopulated_fields = {'slug': ('store_name',)}  # auto-fills slug from store_name
    actions = ['approve_vendors']

    @admin.action(description='Approve selected vendors')
    def approve_vendors(self, request, queryset):
        queryset.update(is_approved=True)
```

**Docs:** https://docs.djangoproject.com/en/6.0/ref/contrib/admin/

---

## 20. Authentication & Authorization

### Authentication = who are you?
### Authorization = what are you allowed to do?

```python
# config/settings/base.py
AUTH_USER_MODEL      = 'accounts.User'   # custom model
LOGIN_URL            = 'accounts:login'  # redirect here if login required
LOGIN_REDIRECT_URL   = 'catalog:home'   # go here after successful login
LOGOUT_REDIRECT_URL  = 'catalog:home'   # go here after logout
```

### Protecting views

```python
# Function-based views — use decorators
from django.contrib.auth.decorators import login_required, permission_required

@login_required                           # redirects to LOGIN_URL if not logged in
def my_orders(request): ...

@permission_required('catalog.add_product')  # needs specific permission
def create_product(request): ...

# Class-based views — use mixins (must be listed FIRST in class definition)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class VendorDashboard(LoginRequiredMixin, UserPassesTestMixin, ListView):
    def test_func(self):
        return self.request.user.is_vendor  # only vendors can see this
```

### Checking roles in templates

```html
{% if user.is_authenticated %}
    <a href="{% url 'orders:my-orders' %}">My Orders</a>
{% endif %}

{% if user.is_vendor %}
    <a href="{% url 'catalog:add-product' %}">Add Product</a>
{% endif %}
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/auth/

---

## 21. Django REST Framework (DRF)

### What is DRF?

DRF turns your Django app into a JSON API so mobile apps, frontend frameworks (React, Vue), and third parties can interact with your data programmatically.

Global defaults in `base.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # API clients
        'rest_framework.authentication.SessionAuthentication',         # browser/admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # require login by default
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

### Serializers — converting between Python objects and JSON

```python
# apps/accounts/serializers.py  (example)
from rest_framework import serializers
from .models import User, VendorProfile

class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VendorProfile
        fields = ['id', 'store_name', 'slug', 'bio', 'rating', 'is_approved']
        read_only_fields = ['rating', 'is_approved']  # clients can't set these

class UserSerializer(serializers.ModelSerializer):
    vendor = VendorProfileSerializer(read_only=True)  # nested serializer

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'role', 'is_verified', 'vendor']
        read_only_fields = ['is_verified']
```

### ViewSets — one class handles all CRUD endpoints

```python
# apps/catalog/views.py  (example)
from rest_framework import viewsets, permissions
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset          = Product.objects.select_related('category', 'seller')
    serializer_class  = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # IsAuthenticatedOrReadOnly: anyone can GET, only logged-in users can POST/PUT/DELETE

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
        # Inject the current user as the seller — clients can't spoof this
```

### Router — auto-generates URLs

```python
# apps/catalog/api_urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
urlpatterns = router.urls
# Auto-generates:
# GET    /api/v1/products/        → list
# POST   /api/v1/products/        → create
# GET    /api/v1/products/<id>/   → retrieve
# PUT    /api/v1/products/<id>/   → update (full)
# PATCH  /api/v1/products/<id>/   → update (partial)
# DELETE /api/v1/products/<id>/   → destroy
```

**Docs:** https://www.django-rest-framework.org/

---

## 22. JWT Authentication

### What is JWT?

A **JSON Web Token** is a signed string that proves a user's identity. Instead of storing a session in the database, the client stores the token locally and sends it with every API request.

```
┌─────────────┐   POST /api/token/              ┌─────────────┐
│   Client    │   {email, password}         →   │   Server    │
│  (React /   │                                  │  (Django)   │
│  mobile)    │ ← {access: "xxx", refresh: "yyy"}│             │
└─────────────┘                                  └─────────────┘
       │
       │  GET /api/v1/products/
       │  Authorization: Bearer xxx          →   validates token
       │ ← [{id: 1, name: "Keyboard"...}]       (no DB lookup needed)
```

```python
# config/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns += [
    path('api/token/',         TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(),    name='token_refresh'),
]
```

```bash
# 1. Get tokens (access expires in 5 min, refresh in 1 day)
POST /api/token/
{"email": "buyer@example.com", "password": "secret"}
→ {"access": "eyJ0...", "refresh": "eyJ0..."}

# 2. Use the access token
GET /api/v1/products/
Authorization: Bearer eyJ0...

# 3. When access token expires, get a new one using the refresh token
POST /api/token/refresh/
{"refresh": "eyJ0..."}
→ {"access": "eyJ0...new..."}
```

**Docs:** https://django-rest-framework-simplejwt.readthedocs.io/

---

## 23. Filtering, Search & Ordering

`django-filter` lets API consumers filter data using URL query parameters without you writing query logic in the view.

```python
# apps/catalog/filters.py
import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    in_stock  = django_filters.BooleanFilter(field_name='stock', lookup_expr='gt',
                                              label='In stock only')

    class Meta:
        model  = Product
        fields = ['category', 'min_price', 'max_price', 'in_stock']
```

```python
class ProductViewSet(viewsets.ModelViewSet):
    filterset_class = ProductFilter
    search_fields   = ['name', 'description', 'seller__email']
    ordering_fields = ['price', 'created_at', 'name']
    ordering        = ['-created_at']  # default sort
```

```bash
# Filter by category and price range
GET /api/v1/products/?category=3&min_price=10&max_price=200

# Full-text search
GET /api/v1/products/?search=mechanical+keyboard

# Sort results
GET /api/v1/products/?ordering=price          # cheapest first
GET /api/v1/products/?ordering=-price         # most expensive first

# Combine everything
GET /api/v1/products/?category=3&search=keyboard&ordering=price&page=2
```

**Docs:** https://django-filter.readthedocs.io/

---

## 24. Signals

### What is a signal?

A signal is Django's publish/subscribe system. Model A can broadcast "I was just saved" without knowing who's listening. Model B can listen and react, without Model A knowing B exists. This keeps apps decoupled.

```python
# apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from .models import Notification

@receiver(post_save, sender=Order)
def notify_seller_on_new_order(sender, instance, created, **kwargs):
    # post_save fires every time an Order is saved
    # created=True only on INSERT, False on UPDATE
    if created:
        Notification.objects.create(
            recipient=instance.product.seller,
            message=f'New order #{instance.id} for "{instance.product.name}"',
        )
```

Connect signals in `AppConfig.ready()` — never at module level:

```python
# apps/notifications/apps.py
class NotificationsConfig(AppConfig):
    name = 'apps.notifications'

    def ready(self):
        import apps.notifications.signals  # noqa: F401
        # This import has a side effect: it registers the @receiver decorators
        # ready() is the right place because it runs after all models are loaded
```

> **Senior tip:** Use signals sparingly. They make code harder to follow because the cause and effect are in different files with no visible connection. Prefer calling service functions directly when you control both sides. Signals shine when you need truly decoupled apps — for example, a `notifications` app that should never import from `orders` directly.

**Docs:** https://docs.djangoproject.com/en/6.0/topics/signals/

---

## 25. Celery & Async Tasks

### What is Celery?

Celery is a background task queue. When a user does something that triggers slow work (sending an email, resizing an image, generating a PDF), you don't make them wait. Instead you hand the work to Celery and return a response immediately. Celery processes the task in a separate worker process.

```
User clicks "Place Order"
        │
   View creates Order, calls task.delay()  ← returns in ~1ms
        │
   View redirects to "Order Confirmed" page
        │
   (Meanwhile, in a separate process...)
   Celery Worker picks up the task
        │
   Sends confirmation email to buyer
   Sends new-order alert to seller
```

### Setup

**[`config/celery.py`](config/celery.py)** — creates the Celery application:

```python
import os
from celery import Celery

# Tell Celery which Django settings to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('markethub')

# Read CELERY_* settings from Django's settings module
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py files in every installed app
app.autodiscover_tasks()
```

**[`config/__init__.py`](config/__init__.py)** — loads Celery when Django starts:

```python
from .celery import app as celery_app
__all__ = ("celery_app",)
```

**Broker configuration** in `base.py`:

```python
CELERY_BROKER_URL    = env('REDIS_URL', default='redis://127.0.0.1:6379')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://127.0.0.1:6379')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

Redis acts as the **broker** — it holds the queue of tasks waiting to be processed.

### Defining tasks

```python
# apps/notifications/tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_order_confirmation(order_id):
    # @shared_task: works with any Celery app (don't hardcode the app name)
    # Always pass IDs, not model instances — the task may run minutes later,
    # and the object may have changed (or even been deleted) by then
    from apps.orders.models import Order
    order = Order.objects.select_related('buyer', 'product').get(id=order_id)
    send_mail(
        subject    = f'Order #{order.id} confirmed',
        message    = f'Thanks for ordering {order.product.name}.',
        from_email = 'noreply@markethub.com',
        recipient_list = [order.buyer.email],
    )
```

### Calling tasks

```python
# apps/orders/views.py
from apps.notifications.tasks import send_order_confirmation

def checkout(request):
    order = Order.objects.create(...)
    send_order_confirmation.delay(order.id)  # .delay() puts it in the queue
    return redirect('orders:confirmation', pk=order.id)
```

### Running a worker

```bash
# In a separate terminal with the venv activated:
celery -A config worker -l info
# -A config  → use the Celery app in config/celery.py
# -l info    → show info-level logs
```

**Docs:** https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

---

## 26. WSGI & ASGI

### What are they?

They are the interfaces between Django and the web server. Think of them as electrical adapters: they let your Django app plug into different server types.

| | WSGI | ASGI |
|---|---|---|
| Stands for | Web Server Gateway Interface | Asynchronous Server Gateway Interface |
| Handles | Traditional HTTP (sync) | HTTP + WebSockets + async views |
| Servers | Gunicorn, uWSGI | Uvicorn, Daphne |
| File | `config/wsgi.py` | `config/asgi.py` |

```python
# config/wsgi.py — used by Gunicorn in production
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_wsgi_application()

# config/asgi.py — used by Uvicorn, or Django Channels for WebSockets
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_asgi_application()
```

```bash
# Production deployment
gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
# or
uvicorn config.asgi:application --workers 4 --host 0.0.0.0 --port 8000
```

**Docs:**
- WSGI: https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
- ASGI: https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/

---

## 27. Environment Variables

### Why never hardcode secrets?

If `SECRET_KEY` or database passwords are in your code, anyone with read access to the git repository has your production credentials. The `.env` file stores secrets locally; `.gitignore` prevents it from ever being committed.

```bash
# .env  ← sits in project root, NEVER committed to git
SECRET_KEY=dev-insecure-change-me-in-production
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://127.0.0.1:6379
ALLOWED_HOSTS=127.0.0.1,localhost
```

`django-environ` reads this file and converts values to the correct Python types automatically:

| Call | `.env` value | Python result |
|---|---|---|
| `env('SECRET_KEY')` | `"abc123"` | `str` |
| `env('DEBUG')` with `(bool, False)` | `"True"` | `True` (bool) |
| `env.list('ALLOWED_HOSTS')` | `"127.0.0.1,localhost"` | `['127.0.0.1', 'localhost']` |
| `env.db('DATABASE_URL')` | `"sqlite:///db.sqlite3"` | `{'ENGINE': ..., 'NAME': ...}` |

> **Senior tip:** In production, do not use a `.env` file at all. Set environment variables directly in your deployment platform (Heroku config vars, AWS Parameter Store, Kubernetes secrets, Docker environment). The `.env` file is a dev convenience — in prod, your deployment platform is the source of truth.

**Docs:** https://django-environ.readthedocs.io/

---

## 28. Tech Stack

| Package | Version | Purpose |
|---|---|---|
| Django | 6.0.5 | Web framework |
| djangorestframework | 3.17.1 | REST API |
| djangorestframework-simplejwt | 5.5.1 | JWT tokens for API auth |
| django-environ | 0.13.0 | `.env` file → Python settings |
| django-filter | 25.2 | Declarative query parameter filters |
| django-extensions | 4.1 | Dev tools: `shell_plus`, `graph_models`, `runserver_plus` |
| celery | 5.6.3 | Distributed background task queue |
| kombu | 5.6.2 | Celery's messaging transport layer |
| psycopg | 3.3.4 | PostgreSQL adapter (async-capable) |
| PyJWT | 2.13.0 | JWT encoding / decoding |
| asgiref | 3.11.1 | ASGI compatibility and sync-to-async bridge |
| cryptography | 48.0.0 | Cryptographic primitives |
| tzdata | 2026.2 | Timezone definitions |

---

## 29. Senior Engineer Tips & Best Practices

These are patterns that separate "it works" from "it works in production at scale."

### Custom User Model — do it first, always

```python
# ✅ Set this before your FIRST migration, never after
AUTH_USER_MODEL = 'accounts.User'
```

Changing the user model after migrations exist is one of the most painful things in Django. It requires squashing migrations, rewriting foreign keys, and often just starting the database fresh. Do it on day one.

---

### Never use `username` as the login field

```python
# ✅ Users think in emails, not usernames
USERNAME_FIELD  = "email"
REQUIRED_FIELDS = ["username"]
```

---

### Always use `TextChoices` / `IntegerChoices` for fixed sets of values

```python
# ❌ Easy to typo, hard to find all valid values
user.role = "vndor"   # silent bug

# ✅ IDE auto-complete, typo-proof, one source of truth
user.role = User.Role.VENDOR
```

---

### Use `update_fields` for partial saves

```python
# ❌ Sends UPDATE with every column — can overwrite concurrent changes
user.role = User.Role.VENDOR
user.save()

# ✅ Sends UPDATE SET role=... — only touches what changed
user.save(update_fields=["role"])
```

---

### Wrap multi-step database operations in `@transaction.atomic`

```python
# ✅ If anything fails, BOTH writes are rolled back — no partial state
@transaction.atomic
def become_vendor(*, user, store_name, bio=""):
    user.role = User.Role.VENDOR
    user.save(update_fields=["role"])
    return VendorProfile.objects.create(user=user, store_name=store_name, ...)
```

---

### Always hash passwords with `set_password()`

```python
# ❌ Stores "hello" in the database as plain text
user.password = "hello"

# ✅ Stores "$pbkdf2-sha256$..." — unrecoverable even if the DB is stolen
user.set_password("hello")
```

---

### Use keyword-only arguments in service functions

```python
# ❌ Positional args: easy to mix up order
register_user("john@test.com", "john", "hunter2")

# ✅ Keyword-only (the * enforces this): explicit at every call site
def register_user(*, email, username, password, role):
    ...
register_user(email="john@test.com", username="john", password="hunter2", role=...)
```

---

### Fix the N+1 query problem with `select_related` / `prefetch_related`

```python
# ❌ 1 query for products + 1 query PER product = potentially thousands of queries
for product in Product.objects.all():
    print(product.seller.email)   # DB hit every iteration

# ✅ 1 query total using a JOIN
for product in Product.objects.select_related('seller'):
    print(product.seller.email)   # no extra DB hits
```

Use `django-debug-toolbar` in development to see every query a page makes — any number above ~10 is a red flag.

---

### Use `db_index=True` on columns you filter or sort by frequently

```python
created_at = models.DateTimeField(auto_now_add=True, db_index=True)
# Without an index: full table scan on every ORDER BY created_at query
# With an index:    near-instant lookup, even on millions of rows
```

---

### Avoid logic in templates

Templates should only format and display data — never compute it.

```html
<!-- ❌ Business logic in template -->
{% if user.role == "vendor" and user.vendor.is_approved and user.vendor.rating > 4.0 %}

<!-- ✅ Logic in Python (model property or service), template just reads it -->
{% if user.can_feature_products %}
```

---

### Keep Celery tasks small and idempotent

```python
# ✅ Pass IDs, not objects. If the task retries, it fetches fresh data.
@shared_task
def send_order_confirmation(order_id):
    order = Order.objects.get(id=order_id)
    ...
# Idempotent: running the same task twice should produce the same result
# (add a guard like: if order.confirmation_sent: return)
```

---

### Structure for security: defence in depth

1. `DEBUG = False` in production — never expose tracebacks
2. `SECRET_KEY` comes from environment, never from code
3. `ALLOWED_HOSTS` set explicitly — prevents HTTP Host header attacks
4. `SECURE_SSL_REDIRECT = True` — force HTTPS
5. `CSRF_COOKIE_SECURE = True` and `SESSION_COOKIE_SECURE = True` — cookies over HTTPS only
6. Use `permission_required` or `UserPassesTestMixin` on every restricted view
7. Never trust user input — always validate with forms or serializers

---

### Use `django-extensions` for productive development

```bash
# Better interactive shell: auto-imports all models
python manage.py shell_plus

# See all SQL queries a shell session makes
python manage.py shell_plus --print-sql

# Visualise your model relationships
python manage.py graph_models -a -o models.png
```
